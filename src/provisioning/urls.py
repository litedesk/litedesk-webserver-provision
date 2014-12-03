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


from django.conf.urls import url, patterns

import views

urlpatterns = patterns(
    'provisioning.views',
    url(r'^users$', views.UserProvisionStatusListView.as_view(), name='user-provision-list'),
    url(r'^data$', views.TenantDataPlanListView.as_view(), name='data-list'),
    url(r'^data/(?P<pk>\d+)$', views.TenantDataPlanView.as_view(), name='data-detail'),
    url(r'^devices$', views.TenantDeviceListView.as_view(), name='device-list'),
    url(r'^devices/(?P<pk>\d+)$', views.TenantDeviceView.as_view(), name='device-detail'),
    url(r'^platforms$', views.TenantPlatformListView.as_view(), name='platform-list'),
    url(r'^platform/(?P<pk>\d+)$', views.TenantPlatformView.as_view(), name='platform-detail'),
    url(r'^software$', views.TenantSoftwareListView.as_view(), name='software-list'),
    url(r'^software/(?P<pk>\d+)$', views.TenantSoftwareView.as_view(), name='software-detail'),
    url(r'^user/(?P<pk>\d+)$$', views.UserProvisionView.as_view(), name='user-provision'),
    url(r'^available_devices$', views.AvailableDeviceListView.as_view(),
        name='available-device-list'),
    url(r'^inventory_entries$', views.InventoryEntryListView.as_view(),
        name='inventory-entries-list'),
)
