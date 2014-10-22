#!/usr/bin/env python
#-*- coding: utf-8 -*-

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


from rest_framework import permissions

import models


class IsTenantPrimaryContact(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        try:
            return request.user.is_authenticated() and request.user.tenant.active
        except:
            return False

    def has_object_permission(self, request, view, obj):
        tenant = obj if isinstance(obj, models.Tenant) else getattr(obj, 'tenant')
        return tenant.active and request.user.tenant == tenant


class IsAdminOrTenantPrimaryContact(IsTenantPrimaryContact):

    def has_object_permission(self, request, view, obj):
        return any([
            request.user.is_superuser,
            super(IsAdminOrTenantPrimaryContact, self).has_object_permission(request, view, obj)
            ])
