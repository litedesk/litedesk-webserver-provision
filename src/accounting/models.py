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
from jsonfield import JSONField
from model_utils import Choices
from model_utils.managers import QueryManager
from model_utils.models import TimeFramedModel, TimeStampedModel

from catalog.models import Offer, CURRENCIES
from tenants.models import Tenant, User


EXPENSE_CATEGORIES = Choices('platform', 'software', 'devices', 'other')


class Contract(TimeFramedModel):
    objects = models.Manager()
    available = QueryManager(end__isnull=True)

    tenant = models.ForeignKey(Tenant)
    quantity = models.PositiveIntegerField(default=1)
    offer = models.ForeignKey(Offer)
    extra = JSONField()

    @property
    def item(self):
        return self.offer.item

    def validate_unique(self, exclude=None):
        item_contracts = self.__class__.available.filter(
                tenant=self.tenant,
                offer__item_type=self.offer.item_type,
                offer__object_id=self.offer.object_id
                )
        if self.pk is not None:
            item_contracts = item_contracts.exclude(id=self.id)

        if item_contracts.exists():
            message = 'Active contract exists related to %s for %s' % (self.item, self.tenant)
            raise ValidationError(message)


class Charge(TimeStampedModel):
    user = models.ForeignKey(User)
    start_date = models.DateField()
    end_date = models.DateField()
    contract = models.ForeignKey(Contract)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=50, choices=CURRENCIES)
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)

    @property
    def item(self):
        return self.contract.item
