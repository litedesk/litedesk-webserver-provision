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

import calendar
import datetime
import logging
from optparse import make_option

from django.core.management.base import BaseCommand
from dateutil.parser import parse

from accounting.models import Contract, Charge
from provisioning.models import UserProvisionHistory


log = logging.getLogger(__name__)


def beginning_of_period(date):
    if date is None: date = datetime.date.today()
    return datetime.date(year=date.year, month=date.month, day=1)


def end_of_period(date):
    if date is None: date = datetime.date.today()
    last_day_of_month = calendar.monthrange(date.year, date.month)[1]
    return datetime.date(year=date.year, month=date.month, day=last_day_of_month)


class Command(BaseCommand):
    help = 'Find all items that provisioned items for the period and derive charge entries'

    option_list = BaseCommand.option_list + (
        make_option('-s', '--start', dest='start_date', default=None, help='start date'),
        make_option('-e', '--end', dest='end_date', default=None, help='end date')
    )

    def handle(self, *fixture_labels, **opts):
        start = beginning_of_period(opts['start_date'] and parse(opts['start_date']).date())
        end = end_of_period(opts['end_date'] and parse(opts['end_date']).date())

        for entry in UserProvisionHistory.objects.exclude(end__lt=start):
            contracts = Contract.available.filter(
                tenant=entry.user.tenant,
                offer__item_type=entry.item_type,
                offer__object_id=entry.object_id
                )
            if not contracts.exists():
                log.info('No contract found for %s' % entry.user.tenant)
                continue
            contract = contracts.get()
            offer = contract.offer.__subclassed__
            charge, created = Charge.objects.get_or_create(
                start_date=start,
                end_date=end,
                user=entry.user,
                contract=contract,
                amount=offer.monthly_cost,
                currency=offer.currency
                )
            if created:
                log.info('Charge %s created' % charge)
            else:
                log.info('Charge %s already recorded' % charge)
