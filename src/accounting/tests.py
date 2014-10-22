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


from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

import factories
import models


class OfferTestCaseMixin(object):
    def _make_offer(self):
        from provisioning.factories import AssetFactory
        item = AssetFactory()
        return self.__class__.FACTORY(
            item_type=ContentType.objects.get_for_model(item),
            object_id=item.id
            )

    def testCanSaveOffer(self):
        self.offer.save()
        self.assertTrue(self.offer.pk is not None)

    def testOfferIsInactiveWhenCreated(self):
        self.offer.save()
        self.assertTrue(self.offer.status == self.offer.STATUS.inactive)

    def testCanActivateOffer(self):
        self.offer.activate()
        self.assertTrue(self.offer.status == self.offer.STATUS.available)

    def testCannotActivateRetiredOffer(self):
        self.offer.retire()
        self.assertRaises(models.CatalogEditionError, self.offer.activate)

    def testCanSuspendAvailableOffer(self):
        self.offer.suspend()
        self.assertTrue(self.offer.status == self.offer.STATUS.suspended)

    def testCannotSuspendedRetiredOffer(self):
        self.offer.retire()
        self.assertRaises(models.CatalogEditionError, self.offer.suspend)


class ProductTestCase(TestCase, OfferTestCaseMixin):
    FACTORY = factories.ProductFactory

    def setUp(self):
        self.offer = self._make_offer()


class SubscriptionTestCase(TestCase, OfferTestCaseMixin):
    FACTORY = factories.SubscriptionFactory

    def setUp(self):
        self.offer = self._make_offer()
