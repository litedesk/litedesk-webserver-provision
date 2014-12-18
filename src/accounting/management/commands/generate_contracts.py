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
from optparse import make_option

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from dateutil.relativedelta import relativedelta

from accounting.factories import ContractFactory
from accounting.models import Contract
from catalog.factories import SubscriptionFactory
from catalog.models import Subscription
from provisioning.models import Asset
from tenants.models import Tenant


log = logging.getLogger(__name__)


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

        start_date = Contract.beginning_of_period(year_ago)
        end_date = Contract.end_of_period(year_from_now)

        for tenant in Tenant.objects.all():
            for service in tenant.tenantservice_set.select_subclasses():
                make_contract(make_offer(service), tenant, start_date, end_date)

            for asset in Asset.objects.filter(tenantasset__tenant=tenant).select_subclasses():
                log.info('Checking/Creating contracts for %s' % asset)
                make_contract(make_offer(asset), tenant, start_date, end_date)
