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

import six

from django.db import models
from django.db.models.fields import related
from django.utils.functional import curry
from django.utils.translation import ugettext_lazy as _

import managers


class ProvisionManyToManyField(models.ManyToManyField):
    description = _('Many-to-many relationship with provisionable objects')

    def contribute_to_class(self, cls, name):
        related_to_self = (self.rel.to == "self" or self.rel.to == cls._meta.object_name)
        if self.rel.symmetrical and related_to_self:
            self.rel.related_name = "%s_rel_+" % name

        super(models.ManyToManyField, self).contribute_to_class(cls, name)

        if not self.rel.through and not cls._meta.abstract and not cls._meta.swapped:
            self.rel.through = related.create_many_to_many_intermediary_model(self, cls)

        setattr(cls, self.name, managers.ProvisionReverseManyRelatedObjectsDescriptor(self))

        self.m2m_db_table = curry(self._get_m2m_db_table, cls._meta)

        if isinstance(self.rel.through, six.string_types):
            def resolve_through_model(field, model, cls):
                field.rel.through = model
            related.add_lazy_relation(cls, self, self.rel.through, resolve_through_model)

    def contribute_to_related_class(self, cls, related):
        if not self.rel.is_hidden() and not related.model._meta.swapped:
            setattr(
                cls,
                related.get_accessor_name(),
                managers.ProvisionManyRelatedObjectsDescriptor(related)
                )

        self.m2m_column_name = curry(self._get_m2m_attr, related, 'column')
        self.m2m_reverse_name = curry(self._get_m2m_reverse_attr, related, 'column')

        self.m2m_field_name = curry(self._get_m2m_attr, related, 'name')
        self.m2m_reverse_field_name = curry(self._get_m2m_reverse_attr, related, 'name')

        get_m2m_rel = curry(self._get_m2m_attr, related, 'rel')
        self.m2m_target_field_name = lambda: get_m2m_rel().field_name
        get_m2m_reverse_rel = curry(self._get_m2m_reverse_attr, related, 'rel')
        self.m2m_reverse_target_field_name = lambda: get_m2m_reverse_rel().field_name
