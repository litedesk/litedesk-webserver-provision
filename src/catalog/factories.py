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

from decimal import Decimal

import factory
from factory import fuzzy

import models


class OfferFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda s: 'Product %s' % s)
    currency = models.CURRENCIES[0][0]
    price = fuzzy.FuzzyDecimal(2.99, 19.90)
    setup_price = Decimal('0.0')

    status = models.Offer.STATUS.available


class ProductFactory(OfferFactory):
    FACTORY_FOR = models.Product


class SubscriptionFactory(OfferFactory):
    FACTORY_FOR = models.Subscription

    period = models.SUBSCRIPTION_PERIODS.month
