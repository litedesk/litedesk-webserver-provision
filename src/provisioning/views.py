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

from itertools import izip
from json import JSONEncoder

from django.contrib.contenttypes.models import ContentType
from django.db import connection
from rest_framework import generics
from rest_framework import permissions as rest_permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer


from tenants import permissions
from tenants.models import TenantService, User
from google import Client
import models
import serializers
from models import TenantAsset
from models import InventoryEntry


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


class UserProvisionStatusListView(APIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    #serializer_class = serializers.UserSummarySerializer

    #def get_queryset(self, *args, **kw):
    def get(self, request, format=None):
        query = '''
        SELECT
            person.id,
            person.display_name,
            person.email,
            ARRAY(
                SELECT tenantservice_id
                FROM tenants_user_services
                WHERE user_id = person.id
            ) AS services,
            ARRAY(
                SELECT DISTINCT asset.name
                FROM provisioning_asset as asset, provisioning_userprovisionable as software
                WHERE asset.id = software.object_id AND software.user_id = person.id
            ) as software,
            ARRAY(
                SELECT entry.serial_number
                FROM provisioning_inventoryentry as entry
                JOIN (
                    SELECT MAX(created) as created, serial_number
                    FROM provisioning_inventoryentry
                    GROUP BY serial_number
                ) as subq
                ON (entry.created = subq.created AND entry.serial_number = subq.serial_number)
                WHERE entry.user_id = person.id AND entry.status = 'handed_out'
            ) as devices
        FROM tenants_user AS person
        WHERE person.tenant_id = %s;
        '''
        cursor = connection.cursor()
        cursor.execute(query, [request.user.tenant.pk])
        column_names = [col[0] for col in cursor.description]
        return Response(data=JSONEncoder().encode([
            dict(izip(column_names, row))
            for row in cursor.fetchall()
        ]))
        #return self.request.user.tenant.user_set.all()


class AvailableDeviceListView(APIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )

    def get(self, request, format=None):
        """
        Return a list of all Available Devices.
        """
        tenant = request.user.tenant
        tenant_assets = TenantAsset.objects.filter(tenant=tenant)
        tenant_assets = [
            ta for ta in tenant_assets
            if ta.asset.__subclassed__.__class__.__name__ == 'Device']
        airwatch_item = models.AirWatch.objects.get(tenant=request.user.tenant)
        google_client = Client(request.user.tenant)
        google_devices = google_client.get_available_devices()
        airwatch_devices = airwatch_item.get_available_devices()
        devices = airwatch_devices + google_devices
        for d in devices:
            for ta in tenant_assets:
                if ta.asset.name.lower() in d['model'].lower():
                    d['tenant_asset_id'] = ta.id
                    d['device_id'] = ta.asset_id

        return Response(devices)


class InventoryEntryListView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.InventoryEntrySerializer
    model = InventoryEntry

    def filter_queryset(self, qs, *args, **kwargs):
        return qs.filter(tenant_asset__tenant=self.request.user.tenant)


class UserInventoryEntryListView(generics.ListAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.InventoryEntrySerializer
    model = InventoryEntry

    def filter_queryset(self, qs, *args, **kwargs):
        return qs.filter(tenant_asset__tenant=self.request.user.tenant,
                         user__id=self.kwargs.get('pk'))


class LatestUserInventoryEntryListView(UserInventoryEntryListView):

    def filter_queryset(self, qs, *args, **kwargs):
        sql = """
            SELECT * FROM {0} as entry
            JOIN (
              SELECT max(created) as created, serial_number
              FROM {0}
              WHERE user_id = %s
              GROUP BY serial_number
            ) as subq
            ON (
              entry.created = subq.created
              AND entry.serial_number = subq.serial_number
            )
        """.format(InventoryEntry._meta.db_table)

        return InventoryEntry.objects.raw(sql, params=[self.kwargs.get('pk')])
        # return qs.filter(tenant_asset__tenant=self.request.user.tenant,
        #                user__id=self.kwargs.get('pk'))
