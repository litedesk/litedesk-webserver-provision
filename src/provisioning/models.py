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


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from autoslug import AutoSlugField
from jsonfield import JSONField
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel

from audit.signals import trackable_model_changed
from tenants.models import Tenant, TenantService, User, UserProvisionable

import okta


class PropertyTable(models.Model):
    metadata = JSONField(null=True)

    def get(self, prop):
        return self.metadata and self.metadata.get(prop)

    def set(self, prop, value):
        if self.metadata is None:
            self.metadata = {}
        self.metadata[prop] = value

    class Meta:
        abstract = True


class Asset(TimeStampedModel):
    objects = InheritanceManager()
    name = models.CharField(max_length=1000)
    slug = AutoSlugField(populate_from='name', unique=False, default='')
    description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class Software(Asset):
    web = models.BooleanField(default=True)
    mobile = models.BooleanField(default=False)
    desktop = models.BooleanField(default=False)


class Device(Asset):
    image = models.ImageField(null=True, blank=True)


class MobileDataPlan(Asset):
    pass


class TenantAsset(PropertyTable):
    tenant = models.ForeignKey(Tenant)
    asset = models.ForeignKey(Asset)

    class Meta:
        unique_together = ('tenant', 'asset')


class Okta(TenantService):
    PLATFORM_TYPE = TenantService.PLATFORM_TYPE_CHOICES.web
    ACTIVE_DIRECTORY_CONTROLLER = True
    domain = models.CharField(max_length=200)

    @property
    def portal_url(self):
        return 'https://%s.okta.com' % self.domain

    @property
    def portal_help_url(self):
        return '%s/help/login' % self.portal_url

    def get_client(self):
        return okta.Client(self.domain, self.api_token)

    def get_service_user(self, user):
        client = self.get_client()
        return client.get(okta.User, user.tenant_email)

    def register(self, user):
        client = self.get_client()
        try:
            client.add_user(user, activate=False)
        except okta.UserAlreadyExistsError:
            pass
        return self.get_service_user(user)

    def activate(self, user):
        client = self.get_client()
        try:
            service_user = self.get_service_user(user)
        except okta.ResourceDoesNotExistError:
            service_user = self.register(user)

        try:
            activation_response = client.activate_user(service_user, send_email=False)
            template_parameters = {
                'user': user,
                'service': self,
                'activation_url': activation_response.get('activationUrl')
            }
            text_msg = render_to_string('mail/text/activation.tmpl.txt', template_parameters)
            html_msg = render_to_string('mail/html/activation.tmpl.html', template_parameters)

            send_mail(
                settings.SITE.get('ACTIVATION_EMAIL_SUBJECT'),
                text_msg,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_msg
            )
        except okta.UserAlreadyActivatedError:
            pass

    def assign(self, asset, user):
        print 'assigning asset %s to %s' % (asset, user)
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=asset)
        client = self.get_client()
        service_user = self.get_service_user(user)
        service_application = client.get(okta.Application, metadata.get('application_id'))
        service_application.assign(service_user, profile=metadata.get('profile'))

    @classmethod
    def get_serializer_data(cls, **data):
        return {
            'domain': data.get('domain')
            }

    class Meta:
        verbose_name = 'Okta'


class AirWatch(TenantService):
    PLATFORM_TYPE = 'mobile'

    username = models.CharField(max_length=80)
    password = models.CharField(max_length=1000)
    server_url = models.URLField()
    group_id = models.CharField(max_length=80)

    @property
    def portal_url(self):
        return self.server_url

    @property
    def portal_help_url(self):
        return None

    def get_client(self):
        from litedesk.lib.airwatch.client import Client
        return Client(
            self.server_url, self.username, self.password, self.api_token
            )

    def get_service_user(self, user):
        client = self.get_client()
        from litedesk.lib.airwatch.user import User
        return User.get_remote(client, user.username)

    def register(self, user):
        client = self.get_client()
        from litedesk.lib.airwatch.user import User, UserAlreadyRegisteredError
        try:
            return User.create(client, user.username)
        except UserAlreadyRegisteredError:
            return self.get_service_user(user)

    def activate(self, user):
        service_user = self.get_service_user(user)
        if service_user is None:
            service_user = self.register(user)
        service_user.activate()

    def assign(self, asset, user):
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=asset)
        service_user = self.get_service_user(user)
        service_user.add_to_group(metadata.get('group_id'))

    @classmethod
    def get_serializer_data(cls, **data):
        return {
            'username': data.get('username'),
            'password': data.get('password'),
            'server_url': data.get('server_url'),
            'group_id': data.get('group_id')
            }


class MobileIron(TenantService):
    PLATFORM_TYPE = 'mobile'


class TenantServiceAsset(PropertyTable):
    service = models.ForeignKey(TenantService)
    asset = models.ForeignKey(Asset)

    @property
    def tenant(self):
        return self.service.tenant

    @property
    def platform(self):
        return self.service.type

    def __unicode__(self):
        return 'Asset %s on %s' % (self.asset, self.service)

    class Meta:
        unique_together = ('service', 'asset')


class UserPlatform(UserProvisionable):
    TRACKABLE_ATTRIBUTES = ['user', 'platform', 'start', 'end']
    platform = models.ForeignKey(TenantService)

    @staticmethod
    def on_user_provision(*args, **kw):
        instance = kw.get('instance')
        user = instance.user
        service = instance.platform
        service.activate(user)

    class Meta:
        unique_together = ('user', 'platform')


class UserDevice(UserProvisionable):
    TRACKABLE_ATTRIBUTES = ['user', 'device', 'start', 'end']
    device = models.ForeignKey(Device)

    class Meta:
        unique_together = ('user', 'device')


class UserSoftware(UserProvisionable):
    TRACKABLE_ATTRIBUTES = ['user', 'software', 'start', 'end']
    software = models.ForeignKey(Software)

    @staticmethod
    def on_user_provision(*args, **kw):
        instance = kw.get('instance')
        user = instance.user
        software = instance.software
        for service in user.platforms.select_subclasses():
            service.assign(software, user)

    class Meta:
        unique_together = ('user', 'software')


class UserMobileDataPlan(UserProvisionable):
    TRACKABLE_ATTRIBUTES = ['user', 'mobile_data_plan', 'start', 'end']
    mobile_data_plan = models.ForeignKey(MobileDataPlan)

    class Meta:
        unique_together = ('user', 'mobile_data_plan')


User.add_to_class('platforms', models.ManyToManyField(TenantService, through=UserPlatform))
User.add_to_class('software', models.ManyToManyField(Software, through=UserSoftware))
User.add_to_class('devices', models.ManyToManyField(Device, through=UserDevice))
User.add_to_class(
    'mobile_data_plans', models.ManyToManyField(MobileDataPlan, through=UserMobileDataPlan)
    )


trackable_model_changed.connect(
    UserPlatform.on_user_provision, dispatch_uid='user_platform_provision', sender=UserPlatform
    )


trackable_model_changed.connect(
    UserSoftware.on_user_provision, dispatch_uid='user_software_provision', sender=UserSoftware
    )


if not getattr(settings, 'PROVISIONABLE_SERVICES'):
    settings.PROVISIONABLE_SERVICES = [
        '.'.join([__name__, k.__name__]) for k in [Okta, AirWatch, MobileIron]
    ]


if not getattr(settings, 'ASSET_CLASSES', []):
    settings.ASSET_CLASSES = [
        '.'.join([__name__, k.__name__]) for k in [Software, Device, MobileDataPlan]
    ]
