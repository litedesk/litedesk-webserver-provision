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
from dateutil.relativedelta import relativedelta

from accounting.models import Contract, Charge
from tenants.models import User


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
        make_option('-e', '--end', dest='end_date', default=None, help='end date'),
        make_option('-u', '--user', dest='user', default=None, help='username')
    )

    def find_charges(self, provision, start, end):
        item = provision.item
        user = provision.user

        # we want to find all charges that one provision action incurs
        # between the period of start and end.

        # We start by finding the earliest point that dates to be looked at.
        begin_interval = max(provision.start.date(), start)
        end_interval = end if provision.end is None else min(provision.end.date(), end)

        current = begin_interval

        # For each month in the begin_interval/end_interval period, we
        # find the contract and record the charge

        while current < end_interval:
            begin_date = beginning_of_period(current)
            end_date = end_of_period(current)
            contract = Contract.objects.valid_offer_for_item(
                user.tenant, item, begin_date, end_date
                )

            if contract is None:
                log.info('No contract for %s on %s-%s' % (user.tenant, begin_date, end_date))
                continue

            offer = contract.offer.__subclassed__
            charge, created = Charge.objects.get_or_create(
                start_date=begin_date,
                end_date=end_date,
                user=user,
                contract=contract,
                amount=offer.monthly_cost,
                currency=offer.currency
                )

            current += relativedelta(months=1)

            if created:
                log.info('%s created' % charge)
            else:
                log.info('%s already recorded' % charge)

    def handle(self, *fixture_labels, **opts):
        start = beginning_of_period(opts['start_date'] and parse(opts['start_date']).date())
        end = end_of_period(opts['end_date'] and parse(opts['end_date']).date())
        username = opts.get('user')

        users = User.objects.all()

        if username: users = users.filter(username=username)

        for user in users:
            for entry in user.userprovisionhistory_set.exclude(end__lt=start):
                self.find_charges(entry, start, end)
