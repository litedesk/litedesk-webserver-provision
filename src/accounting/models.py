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

from django.db import models
from django.core.exceptions import ValidationError
from model_utils import Choices
from model_utils.models import TimeStampedModel

from catalog.models import Offer, CURRENCIES
from tenants.models import Tenant, User


EXPENSE_CATEGORIES = ['platform', 'software', 'devices', 'other']
CATEGORY_CHOICES = Choices(*EXPENSE_CATEGORIES)


class DateFramedModel(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

    def clean(self):
        if self.start_date > self.end_date:
            raise ValidationError('start date must be before end date')

    class Meta:
        abstract = True


class DateFramedQuerySet(models.QuerySet):
    def valid_between(self, start_date, end_date):
        try:
            return self.exclude(start_date__gte=end_date, end_date__lte=start_date).get()
        except models.DoesNotExist:
            return None


class Contract(DateFramedModel):
    objects = models.Manager.from_queryset(DateFramedQuerySet)()

    tenant = models.ForeignKey(Tenant)
    quantity = models.PositiveIntegerField(default=1)
    offer = models.ForeignKey(Offer)
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default=CATEGORY_CHOICES.other
        )

    @property
    def item(self):
        return self.offer.item

    def validate_unique(self, exclude=None):

        item_contract = self.__class__.objects.filter(
                tenant=self.tenant,
                offer__item_type=self.offer.item_type,
                offer__object_id=self.offer.object_id
                ).valid_between(self.start_date, self.end_date)

        if item_contract is not None and item_contract.pk != self.pk:
            message = 'Active contract exists related to %s for %s' % (self.item, self.tenant)
            raise ValidationError(message)

    def __unicode__(self):
        return 'Contract for %s on %s' % (self.tenant, self.item)


class Charge(TimeStampedModel, DateFramedModel):
    user = models.ForeignKey(User, editable=False)
    contract = models.ForeignKey(Contract, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    currency = models.CharField(max_length=50, choices=CURRENCIES, editable=False)

    @property
    def item(self):
        return self.contract.item

    def __unicode__(self):
        return 'Charge on %s (%s) for %s on %s to %s' % (
            self.user, self.user.tenant, self.item, self.start_date, self.end_date
            )
