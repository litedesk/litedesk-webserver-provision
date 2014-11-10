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

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework.compat import smart_text
from rest_framework import serializers

from tenants.models import TenantService, User

import models


__services = TenantService.get_available()
SERVICE_NAMES = [(s.slug, s.name) for s in __services]
SERVICE_MODELS = dict([(s.slug, s.model_class) for s in __services])

BASE_PLATFORM_FIELDS = ['url', 'is_active', 'api_token', 'type', 'service', 'name']


def make_new_service(service_type, tenant, api_token, active, *args, **kw):
    klass = SERVICE_MODELS.get(service_type)
    return klass.make(tenant, api_token, active, **kw)


class ModelRelatedChoiceField(serializers.PrimaryKeyRelatedField):
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

    def field_to_native(self, obj, field_name):
        field = self.source or field_name
        queryset = getattr(obj, field)
        if not hasattr(queryset, 'current'):
            raise AttributeError(
                '%s does not have %s to list current provisioned items' % (obj, field)
                )

        return [self.to_native(item.provisioned_item.pk) for item in queryset.current()]


# We cheat a little bit on the fact that both auth.models.User
# and tenants.models.User will have a reference to tenant, and they
# will be the same. So the choices are based on the
# tenant, and that automatically will limit the possible values
# available for selection. If for some reason one user can access
# more than one tenant, we should review them.

class UserPlatformChoiceField(ModelRelatedChoiceField):

    def _get_choices(self):
        if not self.parent: return []
        request = self.parent.context.get('request')
        return [(x.id, unicode(x)) for x in self.get_choices_queryset(request.user)]

    def get_choices_queryset(self, obj):
        return obj.tenant.tenantservice_set.filter(is_active=True)

    choices = property(_get_choices, serializers.PrimaryKeyRelatedField._set_choices)


class UserAssetChoiceField(ModelRelatedChoiceField):
    def __init__(self, *args, **kw):
        self.asset_class = kw.pop('asset', models.Asset)
        super(UserAssetChoiceField, self).__init__(*args, **kw)

    def _get_choices(self):
        if not self.parent: return []
        request = self.parent.context.get('request')
        return [(x.id, unicode(x)) for x in self.get_choices_queryset(request.user)]

    def get_choices_queryset(self, obj):
        return self.asset_class.objects.filter(tenantasset__tenant=obj.tenant)

    choices = property(_get_choices, serializers.PrimaryKeyRelatedField._set_choices)


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


class UserDeviceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='device__name')

    class Meta:
        model = models.UserDevice
        fields = ('id', 'name')


class UserProvisionSerializer(serializers.ModelSerializer):
    platforms = UserPlatformChoiceField()
    software = UserAssetChoiceField(asset=models.Software)
    devices = UserAssetChoiceField(asset=models.Device)
    simcards = UserAssetChoiceField(asset=models.MobileDataPlan, source='mobile_data_plans')

    def _update_m2m(self, m2m_field_name):
        request = self.context.get('request')
        editor = request.user

        manager = getattr(self.object, m2m_field_name)
        current = manager.current()
        selected = self.object._m2m_data.get(m2m_field_name)

        to_add = [it for it in selected if it not in current]
        to_remove = [it for it in current if it not in selected]

        manager.remove(*to_remove, editor=editor)
        manager.add(*to_add, editor=editor)

    def save_object(self, obj, **kw):
        self._update_m2m('software')
        self._update_m2m('devices')
        self._update_m2m('mobile_data_plans')

        # platforms come last, so we can be sure that all
        # software/devices/simcards are properly defined.
        self._update_m2m('platforms')

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
            self._serialize_asset(ud.id, ud.device.name)
            for ud in obj.userdevice_set.current()
            ]

    def get_user_software(self, obj):
        return [
            self._serialize_asset(us.id, us.software.name)
            for us in obj.usersoftware_set.current()
            ]

    def get_user_mobile_data_plans(self, obj):
        return [
            self._serialize_asset(us.id, us.mobile_data_plan.name)
            for us in obj.usermobiledataplan_set.current()
            ]

    def get_user_platforms(self, obj):
        provisioned = set([svc.type for svc in obj.platforms.select_subclasses()])
        return {k: k in provisioned for k in models.TenantService.PLATFORM_TYPES}

    class Meta:
        model = User
        exclude = ('mobile_data_plans', 'last_modified', 'tenant')
