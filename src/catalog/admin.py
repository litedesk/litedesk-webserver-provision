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

import models


class OfferAdmin(admin.ModelAdmin):
    list_display = ('item', 'status', 'item_type', 'price', 'setup_price', 'currency')
    list_filter = ('item_type', 'status', 'currency')


@admin.register(models.Subscription)
class SubscriptionAdmin(OfferAdmin):
    list_filter = ('item_type', 'status', 'period', 'currency')


@admin.register(models.Product)
class Product(OfferAdmin):
    pass
