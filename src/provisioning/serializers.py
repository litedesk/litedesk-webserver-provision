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

import logging

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework.compat import smart_text
from rest_framework import serializers

from tenants.models import TenantService, User

import models

log = logging.getLogger(__name__)
__services = TenantService.get_available()
SERVICE_NAMES = [(s.slug, s.name) for s in __services]
SERVICE_MODELS = dict([(s.slug, s.model_class) for s in __services])

BASE_PLATFORM_FIELDS = ['url', 'is_active', 'api_token', 'type', 'service', 'name']


def make_new_service(service_type, tenant, api_token, active, *args, **kw):
    klass = SERVICE_MODELS.get(service_type)
    return klass.make(tenant, api_token, active, **kw)


class UserModelChoiceField(serializers.PrimaryKeyRelatedField):
    many = True

    def from_native(self, data):
        queryset = self.get_choices_queryset(self.parent.object)

        try:
            return queryset.get(pk=data)
        except ObjectDoesNotExist:
            msg = self.error_messages['does_not_exist'] % smart_text(data)
            raise ValidationError(msg)
        except (TypeError, ValueError):
            received = type(data).__name__
            msg = self.error_messages['incorrect_type'] % received
            raise ValidationError(msg)

    def _get_choices(self):
        if not self.parent: return []
        request = self.parent.context.get('request')
        return [(x.id, unicode(x)) for x in self.get_choices_queryset(request.user)]

    def _get_field_list(self, data, field_name):
        try:
            return data.getlist(field_name)
        except AttributeError:
            return data.get(field_name)

    choices = property(_get_choices, serializers.PrimaryKeyRelatedField._set_choices)


class UserPlatformChoiceField(UserModelChoiceField):
    def initialize(self, parent, field_name):
        super(UserModelChoiceField, self).initialize(parent, field_name)
        self.queryset = self.get_choices_queryset(self.parent.object)

    def get_choices_queryset(self, obj):
        return obj.tenant.tenantservice_set.filter(is_active=True)

    def field_from_native(self, data, files, field_name, reverted_data):
        value = self._get_field_list(data, field_name)
        reverted_data[field_name] = [self.from_native(it) for it in value]
        return reverted_data


class UserAssetChoiceField(UserModelChoiceField):
    def __init__(self, *args, **kw):
        self.asset_class = kw.pop('asset', models.Asset)
        super(UserModelChoiceField, self).__init__(*args, **kw)

    def initialize(self, parent, field_name):
        super(serializers.RelatedField, self).initialize(parent, field_name)
        self.queryset = self.get_choices_queryset(self.parent.object)

    def get_choices_queryset(self, obj):
        return self.asset_class.objects.filter(tenantasset__tenant=obj.tenant)

    def field_to_native(self, obj, field_name):
        return [
            self.to_native(it.pk)
            for it in obj.get_provisioned_items(item_class=self.asset_class)
            ]

    def field_from_native(self, data, files, field_name, reverted_data):
        ids = self._get_field_list(data, field_name)
        reverted_data[field_name] = self.asset_class.objects.filter(id__in=ids)
        return reverted_data


class NewTenantPlatformSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='platform-detail')
    type = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    service = serializers.ChoiceField(choices=SERVICE_NAMES)
    api_token = serializers.CharField()
    domain = serializers.CharField(required=False, write_only=True)
    username = serializers.CharField(required=False, write_only=True)
    password = serializers.CharField(required=False, write_only=True)
    server_url = serializers.URLField(required=False, write_only=True)
    group_id = serializers.CharField(required=False, write_only=True)
    is_active = serializers.BooleanField(required=False)

    def restore_object(self, attrs, instance=None):
        request = self.context.get('request')
        tenant = request.user.tenant
        service_type = attrs.pop('service')
        api_token = attrs.pop('api_token')
        active = attrs.pop('is_active', True)

        if instance is None:
            instance = make_new_service(service_type, tenant, api_token, active, **attrs)
        else:
            instance.api_token = api_token
            instance.is_active = active

        return instance

    class Meta:
        model = TenantService
        exclude = ('tenant', )


class TenantPlatformSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='platform-detail')
    name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    service = serializers.CharField(read_only=True)

    class Meta:
        model = TenantService
        fields = BASE_PLATFORM_FIELDS


class OktaTenantPlatformSerializer(TenantPlatformSerializer):
    class Meta:
        model = models.Okta
        fields = BASE_PLATFORM_FIELDS + ['domain']


class AirWatchTenantPlatformSerializer(TenantPlatformSerializer):
    class Meta:
        model = models.AirWatch
        fields = BASE_PLATFORM_FIELDS + ['username', 'password', 'server_url', 'group_id']


class TenantAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Asset
        fields = ('id', 'name', 'description')


class UserProvisionSerializer(serializers.ModelSerializer):
    platforms = UserPlatformChoiceField(source='services')
    software = UserAssetChoiceField(asset=models.Software)
    devices = UserAssetChoiceField(asset=models.Device)
    simcards = UserAssetChoiceField(asset=models.MobileDataPlan)

    def _update_provisioned(self, field_name, service):
        request = self.context.get('request')
        editor = request.user
        provision_data = getattr(self.object, '_provision_data', {})

        if field_name not in provision_data:
            return

        item_class = self.fields[field_name].asset_class
        selected = self.object._provision_data.get(field_name)
        current = self.object.get_provisioned_items(item_class=item_class, service=service)

        to_add = [
            item for item in [it.__subclassed__ for it in selected if it not in current]
            if item.can_be_managed_by(service)
        ]
        to_remove = [
            item for item in [it.__subclassed__ for it in current if it not in selected]
            if item.can_be_managed_by(service)
        ]

        for item in to_add:
            log.debug('Adding %s to %s' % (item, service))
            item.provision(service, self.object, editor=editor)

        for item in to_remove:
            log.debug('Removing %s from %s' % (item, service))
            item.deprovision(service, self.object, editor=editor)

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance._provision_data = attrs
        return instance

    def save_object(self, obj, **kw):
        request = self.context.get('request')
        for service in obj.tenant.tenantservice_set.select_subclasses():
            self._update_provisioned('software', service)
            self._update_provisioned('devices', service)
            self._update_provisioned('simcards', service)
        obj.services = self.object._provision_data.get('platforms', [])
        obj.save(editor=request.user)
        return obj

    class Meta:
        model = User
        fields = ('platforms', 'software', 'devices', 'simcards')


class UserSummarySerializer(serializers.ModelSerializer):
    devices = serializers.SerializerMethodField('get_user_devices')
    software = serializers.SerializerMethodField('get_user_software')
    simcards = serializers.SerializerMethodField('get_user_mobile_data_plans')
    platforms = serializers.SerializerMethodField('get_user_platforms')
    display_name = serializers.CharField()

    def _serialize_asset(self, key, value):
        return {
            'id': key,
            'name': value
            }

    def get_user_devices(self, obj):
        return [
            self._serialize_asset(it)
            for it in obj.get_provisioned_items(item_class=models.Device)
            ]

    def get_user_software(self, obj):
        return [
            self._serialize_asset(it)
            for it in obj.get_provisioned_items(item_class=models.Software)
            ]

    def get_user_mobile_data_plans(self, obj):
        return [
            self._serialize_asset(it)
            for it in obj.get_provisioned_items(item_class=models.MobileDataPlan)
            ]

    def get_user_platforms(self, obj):
        provisioned = set([svc.type for svc in obj.services.all()])
        return {k: k in provisioned for k in models.TenantService.PLATFORM_TYPES}

    class Meta:
        model = User
        exclude = ('mobile_data_plans', 'last_modified', 'tenant', 'services')
