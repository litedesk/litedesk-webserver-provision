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
from django.db import transaction
from django.contrib.auth.models import User as UserAccount
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from model_utils.models import TimeStampedModel
from picklefield.fields import PickledObjectField

from signals import trackable_model_changed


class UntrackableChangeError(Exception):
    pass


class AuditLogEntry(TimeStampedModel):
    edited_by = models.ForeignKey(UserAccount)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    data = PickledObjectField(null=True)


class Trackable(TimeStampedModel):
    TRACKABLE_ATTRIBUTES = []
    changelog = GenericRelation(AuditLogEntry)

    @property
    def _trackable_attributes(self):
        return {attr: getattr(self, attr) for attr in self.TRACKABLE_ATTRIBUTES}

    def save(self, editor=None, *args, **kw):
        if editor is None:
            raise UntrackableChangeError('No account defined as author of update')

        original = None if self.pk is None else self.__class__.objects.get(id=self.id)
        with transaction.atomic():
            super(Trackable, self).save(*args, **kw)
            AuditLogEntry.objects.create(
                edited_by=editor,
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.id,
                data=original and original._trackable_attributes
                )
        trackable_model_changed.send(
            sender=self.__class__,
            editor=editor,
            created=original is None,
            instance=self,
            original=original
        )

    class Meta:
        abstract = True
