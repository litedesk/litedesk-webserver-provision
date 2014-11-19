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

from dateutil.relativedelta import relativedelta
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from model_utils import Choices
from model_utils.managers import InheritanceManager, QueryManager
from model_utils.models import TimeStampedModel
from model_utils.fields import StatusField


CURRENCIES = (
    ('EUR', 'Euro'),
    ('USD', 'US Dollar'),
    )
SUBSCRIPTION_PERIODS = Choices('day', 'week', 'month', 'year')


class CatalogEditionError(Exception):
    pass


class Offer(TimeStampedModel):
    STATUS = Choices('inactive', 'available', 'retired', 'suspended')

    objects = InheritanceManager()
    available = QueryManager(status='available')

    name = models.CharField(max_length=500)
    currency = models.CharField(max_length=50, choices=CURRENCIES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    setup_price = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    item_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_type', 'object_id')
    status = StatusField()

    @property
    def is_available(self):
        return self.status == self.STATUS.available

    @property
    def price_string(self):
        return '%s%s' % (self.currency, self.price)

    @property
    def __subclass__(self):
        return Offer.objects.get_subclass(id=self.id)

    def activate(self):
        if self.status == self.STATUS.retired:
            raise CatalogEditionError('Can not activate a retired item')

        if self.status in [self.STATUS.inactive, self.STATUS.suspended]:
            self.status = self.STATUS.available
            self.save()

    def retire(self):
        self.status = self.STATUS.retired
        self.save()

    def suspend(self):
        if self.status == self.STATUS.retired:
            raise CatalogEditionError('Can not suspend a retired item')

        if self.status in [self.STATUS.inactive, self.STATUS.available]:
            self.status = self.STATUS.suspended
            self.save()

    def make_payments(self, start_date=None, end_date=None):
        yield Payment(self.price, self.currency, due_date=start_date)
        raise StopIteration

    def __unicode__(self):
        return '%s (%s)' % (self.item, self.price_string)


class Subscription(Offer):
    period = models.CharField(max_length=30, choices=SUBSCRIPTION_PERIODS)

    @property
    def price_string(self):
        return '%s%s/%s' % (self.currency, self.price, self.period)

    def make_payments(self, start_date=None, end_date=None):
        start_date = start_date or datetime.datetime.now()
        end_date = end_date or start_date + relativedelta(years=1)
        if start_date >= end_date:
            raise ValueError('Subscription start date is set to after it ends.')
        payment_date = start_date
        interval = {
            SUBSCRIPTION_PERIODS.day: relativedelta(days=1),
            SUBSCRIPTION_PERIODS.week: relativedelta(days=7),
            SUBSCRIPTION_PERIODS.month: relativedelta(months=1),
            SUBSCRIPTION_PERIODS.year: relativedelta(years=1)
            }[self.period]

        while payment_date < end_date:
            payment_date += interval
            yield Payment(self.price, self.currency, due_date=payment_date)

        raise StopIteration


class Product(Offer):
    pass


class Payment(object):
    def __init__(self, amount, currency, due_date=None):
        self.amount = amount
        self.currency = currency
        self.due_date = due_date or datetime.datetime.now()
