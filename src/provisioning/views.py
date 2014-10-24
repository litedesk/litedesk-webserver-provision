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


from django.contrib.contenttypes.models import ContentType
from rest_framework import generics
from rest_framework import permissions as rest_permissions

from tenants import permissions
from tenants.models import TenantService, User

import models
import serializers


class TenantPlatformListView(generics.ListCreateAPIView):
    permission_classes = (rest_permissions.IsAuthenticated, )
    serializer_class = serializers.NewTenantPlatformSerializer
    queryset = TenantService.objects.select_subclasses()

    def filter_queryset(self, qs, *args, **kw):
        return qs.filter(tenant__primary_contact=self.request.user)


class TenantPlatformView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )

    def get_serializer_class(self, *args, **kw):
        return {
            'okta': serializers.OktaTenantPlatformSerializer,
            'air-watch': serializers.AirWatchTenantPlatformSerializer
            }.get(self.object.service, serializers.TenantPlatformSerializer)

    def get_object(self, *args, **kw):
        return TenantService.objects.get_subclass(pk=self.kwargs.get('pk'))


class TenantAssetListView(generics.ListAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.TenantAssetSerializer
    ASSET_CLASS = models.Asset

    def get_queryset(self, *args, **kw):
        tenant = self.request.user.tenant
        return self.ASSET_CLASS.objects.filter(tenantasset__tenant=tenant)


class TenantAssetView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAdminOrTenantPrimaryContact, )
    serializer_class = serializers.TenantAssetSerializer
    ASSET_CLASS = models.Asset

    def get_object(self, *args, **kw):
        asset_type = ContentType.objects.get_for_model(self.ASSET_CLASS)
        return self.request.user.tenant.tenantitem_set.get(
            content_type=asset_type, object_id=self.kwargs.get('pk')
            )


class TenantDeviceListView(TenantAssetListView):
    ASSET_CLASS = models.Device


class TenantDeviceView(TenantAssetView):
    ASSET_CLASS = models.Device


class TenantSoftwareListView(TenantAssetListView):
    ASSET_CLASS = models.Software


class TenantSoftwareView(TenantAssetView):
    ASSET_CLASS = models.Software


class TenantDataPlanListView(TenantAssetListView):
    ASSET_CLASS = models.MobileDataPlan


class TenantDataPlanView(TenantAssetView):
    ASSET_CLASS = models.MobileDataPlan


class UserProvisionView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.UserProvisionSerializer
    model = User


class UserProvisionStatusListView(generics.ListAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.UserSummarySerializer

    def get_queryset(self, *args, **kw):
        return self.request.user.tenant.user_set.all()
