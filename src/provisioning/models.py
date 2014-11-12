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

import datetime
import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from autoslug import AutoSlugField
from jsonfield import JSONField
from model_utils import Choices
from model_utils.managers import InheritanceManager
from model_utils.models import TimeFramedModel, TimeStampedModel, StatusModel
from litedesk.lib import airwatch

from audit.models import Trackable
from tenants.models import Tenant, TenantService, User

from fields import ProvisionManyToManyField
import okta


log = logging.getLogger(__name__)


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
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=asset)
        client = self.get_client()
        service_user = self.get_service_user(user)
        service_application = client.get(okta.Application, metadata.get('application_id'))
        try:
            service_application.assign(service_user, profile=metadata.get('profile'))
        except Exception, why:
            log.warn('Error when assigning %s to %s: %s' % (asset, user, why))

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

        return airwatch.client.Client(
            self.server_url, self.username, self.password, self.api_token
            )

    def get_service_user(self, user):
        client = self.get_client()
        service_user = airwatch.user.User.get_remote(client, user.username)
        if service_user is None:
            service_user = airwatch.user.User.create(client, user.username)
        return service_user

    def register(self, user):
        client = self.get_client()
        try:
            return airwatch.user.User.create(client, user.username)
        except airwatch.user.UserAlreadyRegisteredError:
            return self.get_service_user(user)

    def activate(self, user):
        service_user = self.get_service_user(user)
        if service_user is None:
            service_user = self.register(user)
        try:
            service_user.activate()
        except airwatch.user.UserAlreadyActivatedError:
            pass

    def assign(self, asset, user):
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=asset)
        service_user = self.get_service_user(user)
        try:
            service_user.add_to_group(metadata.get('group_id'))
        except airwatch.user.UserAlreadyEnrolledError:
            pass

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


class UserProvisionable(Trackable, TimeFramedModel, StatusModel):
    STATUS = Choices('staged', 'active', 'suspended', 'deprovisioned')
    TRACKABLE_ATTRIBUTES = ['user', 'start', 'end', 'status', 'status_changed']

    user = models.ForeignKey(User)

    @property
    def tenant(self):
        return self.user.tenant

    @property
    def is_provisionable(self):
        return self.end is None

    @property
    def is_active(self):
        return self.status == UserProvisionable.STATUS.active

    @property
    def provisioned_item(self):
        if hasattr(self.__class__, 'PROVISIONABLE_ITEM_FIELD_NAME'):
            return getattr(self, self.__class__.PROVISIONABLE_ITEM_FIELD_NAME)

        base_attrs = set(UserProvisionable.TRACKABLE_ATTRIBUTES)
        extra_attr = (set(self.__class__.TRACKABLE_ATTRIBUTES) - base_attrs).pop()
        return getattr(self, extra_attr)

    def activate(self, editor=None):
        self.status = UserProvisionable.STATUS.active
        self.save(editor=editor)

    def suspend(self, editor=None):
        self.status = UserProvisionable.STATUS.suspended
        self.save(editor=editor)

    def deprovision(self, editor=None):
        self.end = datetime.datetime.now()
        self.save(editor=editor)

    def provision(self, editor=None):
        raise NotImplementedError

    class Meta:
        abstract = True


class UserPlatform(UserProvisionable):
    TRACKABLE_ATTRIBUTES = UserProvisionable.TRACKABLE_ATTRIBUTES + ['platform']
    platform = models.ForeignKey(TenantService)

    def activate(self, editor=None):
        platform = self.platform.__subclass__
        platform.activate(self.user)
        self.status = UserProvisionable.STATUS.active
        self.save(editor=editor)


    def provision(self, editor=None):
        if not self.is_active:
            self.activate(editor=editor)

        for us in self.user.software.current():
            us.provision(editor=editor)


class UserDevice(UserProvisionable):
    TRACKABLE_ATTRIBUTES = UserProvisionable.TRACKABLE_ATTRIBUTES + ['device']
    device = models.ForeignKey(Device)


class UserSoftware(UserProvisionable):
    TRACKABLE_ATTRIBUTES = UserProvisionable.TRACKABLE_ATTRIBUTES + ['software']
    software = models.ForeignKey(Software)

    def provision(self, editor=None):
        self.activate(editor=editor)
        for up in self.user.platforms.current():
            platform = up.platform.__subclass__
            platform.assign(self.software, self.user)


class UserMobileDataPlan(UserProvisionable):
    TRACKABLE_ATTRIBUTES = UserProvisionable.TRACKABLE_ATTRIBUTES + ['mobile_data_plan']
    mobile_data_plan = models.ForeignKey(MobileDataPlan)


User.add_to_class('platforms', ProvisionManyToManyField(TenantService, through=UserPlatform))
User.add_to_class('software', ProvisionManyToManyField(Software, through=UserSoftware))
User.add_to_class('devices', ProvisionManyToManyField(Device, through=UserDevice))
User.add_to_class(
    'mobile_data_plans', ProvisionManyToManyField(MobileDataPlan, through=UserMobileDataPlan)
    )


if not getattr(settings, 'PROVISIONABLE_SERVICES'):
    settings.PROVISIONABLE_SERVICES = [
        '.'.join([__name__, k.__name__]) for k in [Okta, AirWatch, MobileIron]
    ]


if not getattr(settings, 'ASSET_CLASSES', []):
    settings.ASSET_CLASSES = [
        '.'.join([__name__, k.__name__]) for k in [Software, Device, MobileDataPlan]
    ]
