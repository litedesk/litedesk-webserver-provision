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
import hashlib

from django.db import models
from django.core.exceptions import ValidationError
from jsonfield import JSONField
from model_utils import Choices
from model_utils.managers import QueryManager
from model_utils.models import TimeStampedModel, StatusModel

from audit.models import Trackable
from catalog.models import Offer, CURRENCIES
from tenants.models import Tenant


class Contract(TimeStampedModel):
    objects = models.Manager()
    available = QueryManager(active=True)

    tenant = models.ForeignKey(Tenant)
    active = models.BooleanField(default=True)
    offer = models.ForeignKey(Offer)
    extra = JSONField()

    @property
    def item(self):
        return self.offer.item

    def validate_unique(self, exclude=None):
        item_contracts = self.__class__.objects.filter(
                tenant=self.tenant,
                offer__item_type=self.offer.item_type,
                offer__object_id=self.offer.object_id
                )
        if self.pk is not None:
            item_contracts = item_contracts.exclude(id=self.id)

        if item_contracts.filter(active=True).exists():
            message = 'Active contract exists related to %s for %s' % (self.item, self.tenant)
            raise ValidationError(message)

    def execute(self, signee):
        for payment in self.offer.__subclassed__.make_payments():
            charge = Charge(
                tenant=self.tenant,
                contract=self,
                amount=payment.amount,
                currency=payment.currency,
                due_on=payment.due_date
                )
            charge.code = charge.generate_code()
            charge.save(editor=signee)


class Charge(Trackable, StatusModel):
    TRACKABLE_ATTRIBUTES = ['amount', 'currency', 'amount_paid', 'due_on', 'paid_on']
    STATUS = Choices('scheduled', 'waived', 'pending', 'paid')

    code = models.CharField(max_length=30, unique=True)
    tenant = models.ForeignKey(Tenant)
    contract = models.ForeignKey(Contract)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=50, choices=CURRENCIES)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    due_on = models.DateTimeField()
    paid_on = models.DateTimeField(null=True)

    @property
    def item(self):
        return self.contract.item

    def generate_code(self):
        hsh = hashlib.sha1()
        hsh.update('-'.join([
            str(self.item.id),
            str(self.tenant.id),
            datetime.datetime.now().isoformat()
        ]))
        return hsh.hexdigest()
