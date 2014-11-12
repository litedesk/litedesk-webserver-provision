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

from django.db.models.fields import related
from django.utils.functional import cached_property


def create_many_provisionable_related_manager(superclass, rel):
    related_manager_class = related.create_many_related_manager(superclass, rel)

    class ProvisionRelatedManager(related_manager_class):

        def add(self, *objs, **kw):
            editor = kw.get('editor')
            for obj in objs:
                m2m_relation = self.through(**{
                    self.target_field_name: obj,
                    self.source_field_name: self.instance,
                    'start': datetime.datetime.now()
                    })
                m2m_relation.save(editor=editor)

        def remove(self, *objs, **kw):
            editor = kw.get('editor')
            for obj in objs:
                obj.deprovision(editor=editor)

        def current(self):
            return self.through._default_manager.filter(end=None)

        def __call__(self, **kwargs):
            manager = getattr(self.model, kwargs.pop('manager'))
            manager_class = create_many_provisionable_related_manager(manager.__class__, rel)
            return manager_class(
                model=self.model,
                query_field_name=self.query_field_name,
                instance=self.instance,
                symmetrical=self.symmetrical,
                source_field_name=self.source_field_name,
                target_field_name=self.target_field_name,
                reverse=self.reverse,
                through=self.through,
                prefetch_cache_name=self.prefetch_cache_name,
            )

    return ProvisionRelatedManager


class ProvisionManyRelatedObjectsDescriptor(related.ManyRelatedObjectsDescriptor):
    @cached_property
    def related_manager_cls(self):
        return create_many_provisionable_related_manager(
            self.related.model._default_manager.__class__,
            self.related.field.rel
        )


class ProvisionReverseManyRelatedObjectsDescriptor(related.ReverseManyRelatedObjectsDescriptor):
    @cached_property
    def related_manager_cls(self):
        return create_many_provisionable_related_manager(
            self.field.rel.to._default_manager.__class__,
            self.field.rel
        )
