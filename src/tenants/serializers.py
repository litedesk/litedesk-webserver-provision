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


from django.contrib.auth import get_user_model
from rest_framework import serializers

import models


class NewUserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')

    def save_object(self, user, *args, **kw):
        request = self.context.get('request')
        user.tenant = request.user.tenant
        return super(NewUserSerializer, self).save_object(user, *args, **kw)

    def validate(self, attrs, *args, **kw):
        request = self.context.get('request')
        tenant = request.user.tenant
        username = attrs.get('username')
        if models.User.objects.filter(tenant=tenant, username=username).exists():
            raise serializers.ValidationError('User %s already exists' % username)
        return attrs

    class Meta:
        model = models.User
        fields = (
            'id', 'first_name', 'last_name', 'display_name',
            'username', 'mobile_phone_number', 'email', 'url'
            )
        read_only_fields = ('id', 'tenant', )


class AccountSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='account', lookup_field='username')

    class Meta:
        model = get_user_model()
        fields = ('url', 'first_name', 'last_name')


class TenantSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Tenant
        fields = ('name', 'active', 'email_domain')


class UserSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')
    tenant_email = serializers.CharField(read_only=True)
    tenant = TenantSerializer(read_only=True)
    groups = serializers.HyperlinkedRelatedField(
        view_name='user-group-detail', source='usergroup_set', many=True, read_only=True
        )
    mobile_phone_number = serializers.CharField(required=False)

    def save_object(self, user, **kw):
        request = self.context.get('request')
        editor = request.user

        user.save(editor=editor)

        # # Need to compare with current status to find which platforms are being added/removed.
        # current_platforms = [p[0] for p in user.assigned_platforms.values_list('platform')]
        # selected_platforms = user._related_data.get('platforms')

        # to_add = [p for p in selected_platforms if p not in current_platforms]
        # to_remove = [p for p in current_platforms if p not in selected_platforms]

        # for platform in to_add:
        #     user.assign_platform(platform, editor=editor)
        # for platform in to_remove:
        #     user.revoke_platform(platform, editor=editor)

        return user

    class Meta:
        model = models.User
        fields = (
            'id', 'url', 'username', 'status', 'first_name', 'last_name', 'display_name',
            'tenant', 'tenant_email', 'email', 'mobile_phone_number', 'groups'
            )
        read_only_fields = ('username', )


class UserGroupSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-group-detail')
    members = serializers.HyperlinkedRelatedField(view_name='user-detail', many=True)

    def get_fields(self, *args, **kw):
        request = self.context.get('request')
        fields = super(UserGroupSerializer, self).get_fields(*args, **kw)
        fields['members'].queryset = request.user.tenant.user_set.all()

        return fields

    def save_object(self, obj, *args, **kw):
        request = self.context.get('request')
        obj.tenant = request.user.tenant
        return super(UserGroupSerializer, self).save_object(obj, *args, **kw)

    class Meta:
        model = models.UserGroup
        exclude = ('tenant', )
