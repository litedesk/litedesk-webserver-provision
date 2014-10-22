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


import random

from django.core.exceptions import ValidationError
from django.test import TestCase

from tenants import factories
from audit.models import UntrackableChangeError
import models


class TrackableTestCaseMixin(object):
    def testCanCreateObject(self):
        self.assertTrue(self.tracked_item.pk is not None)

    def testCreationDoesNotCreateAuditLog(self):
        self.assertTrue(self.tracked_item.changelog.count() == 0)

    def testEditorCanUpdateObject(self):
        self.tracked_item.save(editor=self.editor)
        self.assertTrue(self.tracked_item.changelog.count() == 1)

    def testCanNotUpdateWithoutEditor(self):
        self.assertRaises(UntrackableChangeError, self.tracked_item.save)


class UserTestCase(TestCase, TrackableTestCaseMixin):
    def setUp(self):
        self.tracked_item = factories.UserFactory()
        self.editor = self.tracked_item.tenant.primary_contact

    # def testCanAssignPlatform(self):
    #     platform = random.choice(models.SOFTWARE_PLATFORMS)
    #     self.tracked_item.assign_platform(platform, editor=self.editor)
    #     self.assertTrue(self.tracked_item.has_access_to_platform(platform))

    # def testCanNotAssignSamePlatformMultipleTimes(self):
    #     platform = random.choice(models.SOFTWARE_PLATFORMS)
    #     self.tracked_item.assign_platform(platform, editor=self.editor)
    #     self.assertRaises(ValidationError, self.tracked_item.assign_platform, platform)

    # def testCanRevokePlatform(self):
    #     platform = random.choice(models.SOFTWARE_PLATFORMS)
    #     self.tracked_item.assign_platform(platform, editor=self.editor)
    #     self.tracked_item.revoke_platform(platform, editor=self.editor)
    #     self.assertFalse(self.tracked_item.has_access_to_platform(platform))

    # def testCanNotRevokeUnassignedPlatform(self):
    #     platform = random.choice(models.SOFTWARE_PLATFORMS)
    #     self.assertRaises(ValidationError, self.tracked_item.revoke_platform, platform)

    # def testCanReassignPlatform(self):
    #     platform = random.choice(models.SOFTWARE_PLATFORMS)
    #     self.tracked_item.assign_platform(platform, editor=self.editor)
    #     self.assertTrue(self.tracked_item.has_access_to_platform(platform))
    #     self.tracked_item.revoke_platform(platform, editor=self.editor)
    #     self.assertFalse(self.tracked_item.has_access_to_platform(platform))
