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
from jsonfield import JSONField
from model_utils import Choices
from model_utils.models import TimeStampedModel, StatusModel

from catalog.models import Offer
from tenants.models import Tenant


class Contract(TimeStampedModel):
    tenant = models.ForeignKey(Tenant)
    active = models.BooleanField(default=True)
    offer = models.ForeignKey(Offer)
    extra = JSONField()

    @property
    def item(self):
        return self.offer.item


class Charge(TimeStampedModel, StatusModel):
    STATUS = Choices('scheduled', 'waived', 'pending', 'paid')

    tenant = models.ForeignKey(Tenant)
    contract = models.ForeignKey(Contract)
