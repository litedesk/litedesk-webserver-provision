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

# from audit.admin import TrackableModelAdminMixin
import models


class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )


@admin.register(models.TenantAsset)
class TenantAssetAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'asset', )
    search_fields = ('asset', )
    list_filter = ('tenant', 'asset')


@admin.register(models.Device)
class DeviceAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Software)
class SoftwareAdmin(admin.ModelAdmin):
    pass


@admin.register(models.MobileDataPlan)
class MobileDataPlanAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Okta)
class OktaAdmin(admin.ModelAdmin):
    pass


@admin.register(models.AirWatch)
class AirWatchAdmin(admin.ModelAdmin):
    pass


@admin.register(models.TenantServiceAsset)
class TenantServiceAssetAdmin(admin.ModelAdmin):
    list_display = ('service', 'asset', )
    list_filter = ('asset', )


@admin.register(models.UserProvisionable)
class UserProvisionableAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', )
    list_filter = ('item_type', )
    search_fields = ('user__username', )
