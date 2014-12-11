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

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models.signals import post_save
from dateutil.relativedelta import relativedelta
from factory.django import mute_signals

from audit.signals import trackable_model_changed
from accounting.factories import ContractFactory
from accounting.models import Contract, Charge
from catalog.factories import SubscriptionFactory
from catalog.models import Subscription
from provisioning.models import Asset, Software, UserProvisionHistory, Okta, AirWatch
from tenants.factories import UserFactory
from tenants.models import User, Tenant


log = logging.getLogger(__name__)

MOBILE_USAGE_PCT = 45.0
APPLE_USAGE_PCT = 30.0
GOOGLE_USAGE_PCT = 30.0
OFFICE_USAGE_PCT = 80.0
SALESFORCE_USAGE_PCT = 25.0
DAILY_HIRING_RATE = 0.5
MONTHLY_FIRING_RATE = 2.0

GOOGLE_PRODUCTS = ['Google', 'Chromebook']


def random_event_test(probability):
    return probability <= (100 * random.random())


def make_offer(asset):
    asset_type = ContentType.objects.get_for_model(asset)
    try:
        return Subscription.objects.get_subclass(item_type=asset_type, object_id=asset.id)
    except:
        return SubscriptionFactory(item_type=asset_type, object_id=asset.id)


def make_contract(offer, tenant, start, end):
    try:
        return tenant.contract_set.filter(offer=offer).valid_between(start, end)
    except Contract.DoesNotExist:
        contract = ContractFactory(offer=offer, tenant=tenant, start_date=start, end_date=end)
        contract.save()
        log.info('Created %s' % contract)
        return contract


def make_user(tenant, hiring_date, end_date):
    with mute_signals(trackable_model_changed, post_save):
        new_user = UserFactory.build(tenant=tenant)
        try:
            user = tenant.user_set.get(username=new_user.username)
        except User.DoesNotExist:
            models.Model.save(new_user)
            user = new_user

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
    models.Model.save(uph)


def make_provision_history(user, start_date, end_date):
    okta = Okta.objects.get(tenant=user.tenant)
    aw = AirWatch.objects.get(tenant=user.tenant)
    user.services.add(okta)

    if random_event_test(MOBILE_USAGE_PCT):
        user.services.add(aw)

    for service in user.services.select_subclasses():
        make_provision_service(user, service, start_date)

    if random_event_test(SALESFORCE_USAGE_PCT):
        for software in Software.objects.filter(name__icontains='salesforce'):
            make_provision_asset(user, software, start_date)

    if random_event_test(OFFICE_USAGE_PCT):
        for software in Software.objects.filter(name__icontains='office365'):
            make_provision_asset(user, software, start_date)

    if random_event_test(APPLE_USAGE_PCT):
        for asset in Asset.objects.filter(name__startswith='i').select_subclasses():
            make_provision_asset(user, asset, start_date)

    if random_event_test(GOOGLE_USAGE_PCT):
        for asset in Asset.objects.filter(name__in=GOOGLE_PRODUCTS).select_subclasses():
            make_provision_asset(user, asset, start_date)

    current = start_date
    while current < end_date:
        current += relativedelta(months=1)
        if random_event_test(MONTHLY_FIRING_RATE):
            log.info('Dismissing %s on %s' % (user, current))
            UserProvisionHistory.objects.filter(user=user, start=start_date).update(end=current)
            break


class Command(BaseCommand):
    help = ''

    def handle(self, *fixture_labels, **opts):
        today = datetime.date.today()
        year_ago = today - relativedelta(years=1)
        year_from_now = today + relativedelta(years=1)

        start_date = Contract.beginning_of_period(year_ago)
        end_date = Contract.end_of_period(year_from_now)

        for tenant in Tenant.objects.all():
            for asset in Asset.objects.filter(tenantasset__tenant=tenant).select_subclasses():
                log.info('Checking/Creating contracts for %s' % asset)
                make_contract(make_offer(asset), tenant, start_date, end_date)

            current = start_date
            # Create a tenant with a few employees from the start.
            for _ in xrange(random.randint(10, 200)):
                make_user(tenant, current, end_date)

            # Every day until end_date, there is a chance of hiring someone else.
            while current < end_date:
                current += relativedelta(days=1)
                if random_event_test(DAILY_HIRING_RATE):
                    make_user(tenant, current, end_date)
