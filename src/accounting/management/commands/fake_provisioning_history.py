#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014, Deutsche Telekom AG - Laboratories (T-Labs)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import logging
import random
from optparse import make_option

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.signals import post_save
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from factory.django import mute_signals

from audit.signals import trackable_model_changed
from accounting.factories import ContractFactory
from accounting.models import Contract
from catalog.factories import SubscriptionFactory
from catalog.models import Subscription
from provisioning.models import Asset, Software, UserProvisionHistory, Okta, AirWatch
from tenants.factories import UserFactory
from tenants.models import Tenant


log = logging.getLogger(__name__)

MOBILE_USAGE_PCT = 45.0
APPLE_USAGE_PCT = 30.0
GOOGLE_USAGE_PCT = 30.0
OFFICE_USAGE_PCT = 80.0
SALESFORCE_USAGE_PCT = 25.0
MONTHLY_FIRING_RATE = 5.0

GOOGLE_PRODUCTS = ['Google', 'Chromebook', 'Chromebox']


def random_event_test(probability):
    return probability > (100 * random.random())


def log_provision(item, user, provision_date):
    log.info('Assigning %s to %s on %s' % (item, user, provision_date.strftime('%d.%m.%Y')))


def make_offer(asset):
    asset_type = ContentType.objects.get_for_model(asset)
    offer = Subscription.available.filter(item_type=asset_type, object_id=asset.id).first()
    return offer or SubscriptionFactory(item_type=asset_type, object_id=asset.id)


def make_contract(offer, tenant, start, end):
    contract = Contract.objects.valid_offer_for_item(tenant, offer.item, start, end)
    if contract is None:
        contract = ContractFactory(offer=offer, tenant=tenant, start_date=start, end_date=end)
        contract.save()
        log.info('Created %s' % contract)
    return contract


def make_user(tenant, hiring_date, end_date):
    with mute_signals(trackable_model_changed, post_save):
        user = UserFactory.build(tenant=tenant)
        if tenant.user_set.filter(username=user.username).exists():
            log.info('User %s already exists. Skipping...' % user)
            return

        models.Model.save(user)
        make_provision_history(user, hiring_date, end_date)


def make_provision_asset(user, asset, provision_date):
    item_type = ContentType.objects.get_for_model(asset)
    for service in user.services.select_subclasses():
        if asset.__subclassed__.can_be_managed_by(service):
            uph = UserProvisionHistory(
                service=service,
                user=user,
                item_type=item_type,
                object_id=asset.id,
                start=provision_date
                )
            log_provision(asset, user, provision_date)
            models.Model.save(uph)


def make_provision_service(user, service, provision_date):
    item_type = ContentType.objects.get_for_model(service)
    uph = UserProvisionHistory(
        service=service,
        user=user,
        item_type=item_type,
        object_id=service.id,
        start=provision_date
    )
    log_provision(service, user, provision_date)
    models.Model.save(uph)


def make_provision_history(user, start_date, end_date):
    okta = Okta.objects.get(tenant=user.tenant)
    aw = AirWatch.objects.get(tenant=user.tenant)
    user.services.add(okta)

    if random_event_test(MOBILE_USAGE_PCT):
        user.services.add(aw)

    if random_event_test(SALESFORCE_USAGE_PCT):
        for software in Software.objects.filter(name__icontains='salesforce'):
            make_provision_asset(user, software, start_date)

    if random_event_test(OFFICE_USAGE_PCT):
        for software in Software.objects.filter(name__icontains='office365'):
            make_provision_asset(user, software, start_date)

    if random_event_test(APPLE_USAGE_PCT):
        user.services.add(aw)
        for asset in Asset.objects.filter(name__startswith='i').select_subclasses():
            make_provision_asset(user, asset, start_date)

    if random_event_test(GOOGLE_USAGE_PCT):
        for asset in Asset.objects.filter(name__in=GOOGLE_PRODUCTS).select_subclasses():
            make_provision_asset(user, asset, start_date)

    for service in user.services.select_subclasses():
        make_provision_service(user, service, start_date)

    current = start_date
    while current < end_date:
        current += relativedelta(months=1)
        if random_event_test(MONTHLY_FIRING_RATE):
            log.info('Dismissing fake user %s on %s' % (user, current))
            user.userprovisionhistory_set.filter(
                end__isnull=True, start=start_date).update(end=current)
            break


class Command(BaseCommand):
    help = ''

    option_list = BaseCommand.option_list + (
        make_option('-n', '--users', dest='users', default=10, help='# users to create'),
        make_option('-s', '--start', dest='start_date', default=None, help='start date'),
        make_option('-e', '--end', dest='end_date', default=None, help='end date')
    )

    def handle(self, *fixture_labels, **opts):
        today = datetime.date.today()
        year_ago = today - relativedelta(years=1)
        year_from_now = today + relativedelta(years=1)

        start_date = Contract.beginning_of_period(
            opts['start_date'] and parse(opts['start_date']).date() or year_ago
            )
        end_date = Contract.end_of_period(
            opts['end_date'] and parse(opts['end_date']).date() or year_from_now
            )

        for tenant in Tenant.objects.all():
            for _ in xrange(int(opts['users'])):
                make_user(tenant, start_date, end_date)
