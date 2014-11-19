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


from django.contrib import admin

from audit.admin import TrackableModelAdminMixin
import models


@admin.register(models.Charge)
class ChargeAdmin(TrackableModelAdminMixin, admin.ModelAdmin):
    list_display = (
        'code', 'tenant', 'item', 'amount', 'currency', 'amount_paid',
        'created', 'due_on', 'paid_on', 'status'
        )
    list_filter = ('tenant', 'status',)
    search_fields = ('code', 'due_on')


@admin.register(models.Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'active', 'offer', 'item')
    list_filter = ('tenant', 'active')
