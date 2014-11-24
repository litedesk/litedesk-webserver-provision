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
import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from autoslug import AutoSlugField
from jsonfield import JSONField
from model_utils import Choices
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel, StatusModel
from litedesk.lib import airwatch

from accounting.models import Contract
from audit.models import Trackable
from catalog.models import Offer
from tenants.models import Tenant, TenantService, User

import okta
from signals import item_provisioned, item_deprovisioned


log = logging.getLogger(__name__)


class Provisionable(object):
    def activate(self, user, **kw):
        raise NotImplementedError

    def deprovision(self, service, user, *args, **kw):
        raise NotImplementedError

    def provision(self, service, user, *args, **kw):
        raise NotImplementedError


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


class TenantProvisionable(PropertyTable):
    tenant = models.ForeignKey(Tenant)
    offer = models.ForeignKey(Offer)


class UserProvisionable(TimeStampedModel, StatusModel):
    STATUS = Choices('staged', 'processing', 'active')
    user = models.ForeignKey(User)
    service = models.ForeignKey(TenantService)
    item_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_type', 'object_id')

    @property
    def tenant(self):
        return self.user.tenant

    def __unicode__(self):
        return '%s provision for user %s on %s' % (self.item, self.user, self.service)

    class Meta:
        unique_together = ('user', 'service', 'item_type', 'object_id')


# class UserPlatform(UserProvisionable):
#     TRACKABLE_ATTRIBUTES = UserProvisionable.TRACKABLE_ATTRIBUTES + ['platform']
#     platform = models.ForeignKey(TenantService)

#     def activate(self, editor=None):
#         platform = self.platform.__subclass__
#         platform.activate(self.user)
#         super(UserPlatform, self).activate(editor=editor)

#     def provision(self, editor=None):
#         if not self.is_active:
#             self.activate(editor=editor)

#         for us in self.user.software.current():
#             self.platform.__subclass__.assign(us.software, self.user)

#     def deprovision(self, editor=None):
#         platform = self.platform.__subclass__
#         if not platform.is_active_directory_controller:
#             platform.deactivate(self.user)
#         super(UserPlatform, self).deprovision(editor=editor)


# class UserSoftware(UserProvisionable):
#     TRACKABLE_ATTRIBUTES = UserProvisionable.TRACKABLE_ATTRIBUTES + ['software']

#     def _get_current_platforms(self):
#         return [up.platform.__subclass__ for up in self.user.platforms.current()]

#     def provision(self, editor=None):
#         for platform in self._get_current_platforms():
#             platform.assign(self.software, self.user)
#         self.activate(editor=editor)

#     def deprovision(self, editor=None):
#         for platform in self._get_current_platforms():
#             platform.unassign(self.software, self.user)
#         super(UserSoftware, self).deprovision(editor=editor)


# class UserMobileDataPlan(UserProvisionable):
#     TRACKABLE_ATTRIBUTES = UserProvisionable.TRACKABLE_ATTRIBUTES + ['mobile_data_plan']


class Asset(TimeStampedModel, Provisionable):
    objects = InheritanceManager()
    name = models.CharField(max_length=1000)
    slug = AutoSlugField(populate_from='name', unique=False, default='')
    description = models.TextField(null=True, blank=True)
    web = models.BooleanField(default=True)
    mobile = models.BooleanField(default=False)
    desktop = models.BooleanField(default=False)

    @property
    def supported_platforms(self):
        return [p for p in ['web', 'mobile', 'desktop'] if getattr(self, p)]

    def provision(self, service, user, editor=None):
        log.debug('Provisioning %s for user %s on %s' % (self, user, service))
        if self.can_be_managed_by(service):
            UserProvisionable.objects.create(
                service=service,
                user=user,
                item_type=ContentType.objects.get_for_model(self),
                object_id=self.id
                )
            item_provisioned.send(
                sender=self.__class__,
                editor=editor,
                instance=self,
                service=service,
                user=user
                )

    def deprovision(self, service, user, editor=None):
        UserProvisionable.objects.filter(
            service=service,
            user=user,
            item_type=ContentType.objects.get_for_model(self),
            object_id=self.id
            ).delete()
        item_deprovisioned.send(
            sender=self.__class__,
            editor=editor,
            instance=self,
            service=service,
            user=user
        )

    def can_be_managed_by(self, service):
        return service.type in self.supported_platforms

    def __unicode__(self):
        return self.name


class Software(Asset):
    def provision(self, service, user, editor=None):
        service.assign(self, user)
        super(Software, self).provision(service, user, editor=editor)

    def deprovision(self, service, user, editor=None):
        service.unassign(self, user)
        super(Software, self).deprovision(service, user, editor=editor)


class Device(Asset):
    image = models.ImageField(null=True, blank=True)

    @property
    def __subclass__(self):
        if 'chrome' in self.name.lower():
            self.__class__ = ChromeDevice
        return self

    def _get_email_template_parameters(self, service, user):
        device = self.__subclass__
        if isinstance(device, ChromeDevice):
            return {
                'user': user,
                'service': service,
                'site': settings.SITE,
                'device': device
                }
        return None

    def _get_email_template(self, service, format='html'):
        extension = {
            'text': 'txt',
            'html': 'html'
        }.get(format, format)
        template_name = None
        if isinstance(self.__subclass__, ChromeDevice):
            template_name = 'activation_chromebook'

        return template_name and 'provisioning/mail/%s/%s.tmpl.%s' % (
            format, template_name, extension
            )

    def provision(self, service, user, editor=None):
        super(Device, self).provision(service, user, editor=editor)
        html_template = self._get_email_template(service, format='html')
        text_template = self._get_email_template(service, format='text')
        if not (html_template or text_template):
            return

        template_parameters = self._get_email_template_parameters(service, user)

        text_msg = render_to_string(text_template, template_parameters)
        html_msg = render_to_string(html_template, template_parameters)

        send_mail(
            '%s - Start using your %s' % (settings.SITE.get('name'), self.name),
            text_msg,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_msg
        )

    def activate(self, user, *args, **kw):
        pass


class MobileDataPlan(Asset):
    pass


class ChromeDevice(Device):
    def can_be_managed_by(self, service):
        return service.type == TenantService.PLATFORM_TYPE_CHOICES.web

    class Meta:
        proxy = True


class TenantAsset(PropertyTable):
    tenant = models.ForeignKey(Tenant)
    asset = models.ForeignKey(Asset)

    class Meta:
        unique_together = ('tenant', 'asset')


class Okta(TenantService, Provisionable):
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

    def set_random_ad_password(self, user):
        remote_user = user.get_remote()
        password = ''.join([
            random.choice(string.ascii_letters + string.digits)
            for n in xrange(8)
        ])
        remote_user.set_password(password)
        return remote_user, password

    def activate(self, user, *args, **kw):
        client = self.get_client()
        try:
            service_user = self.get_service_user(user)
        except okta.ResourceDoesNotExistError:
            service_user = self.register(user)

        try:
            ad_user, password = self.set_random_ad_password(user)
            activation_response = client.activate_user(service_user, send_email=False)
            ad_user.activate()
            ad_user.save()
            template_parameters = {
                'user': user,
                'service': self,
                'activation_url': activation_response.get('activationUrl'),
                'site': settings.SITE,
                'password': password
            }
            text_msg = render_to_string(
                'provisioning/mail/text/activation_okta.tmpl.txt', template_parameters
                )
            html_msg = render_to_string(
                'provisioning/mail/html/activation_okta.tmpl.html', template_parameters
                )

            send_mail(
                '%s - Welcome to %s' % (settings.SITE.get('name'), self.name),
                text_msg,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_msg
            )
        except okta.UserAlreadyActivatedError:
            pass

    def deactivate(self, user):
        log.warn('Trying to deactivate user %s on Okta, which should never happen' % user)
        return

    def assign(self, asset, user):
        log.debug('Assigning %s to %s on Okta' % (asset, user))
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=asset)
        client = self.get_client()
        service_user = self.get_service_user(user)
        service_application = client.get(okta.Application, metadata.get('application_id'))
        try:
            service_application.assign(service_user, profile=metadata.get('profile'))
        except Exception, why:
            log.warn('Error when assigning %s to %s: %s' % (asset, user, why))

    def unassign(self, asset, user):
        log.debug('Removing %s from %s on Okta' % (asset, user))
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=asset)
        client = self.get_client()
        service_user = self.get_service_user(user)
        service_application = client.get(okta.Application, metadata.get('application_id'))
        try:
            service_application.unassign(service_user)
        except Exception, why:
            log.warn('Error when unassigning %s to %s: %s' % (asset, user, why))

    @classmethod
    def get_serializer_data(cls, **data):
        return {
            'domain': data.get('domain')
            }

    class Meta:
        verbose_name = 'Okta'


class AirWatch(TenantService, Provisionable):
    PLATFORM_TYPE = 'mobile'

    username = models.CharField(max_length=80)
    password = models.CharField(max_length=1000)
    server_url = models.URLField()
    group_id = models.CharField(max_length=80)

    @property
    def portal_url(self):
        url = self.server_url
        if url.endswith('/'):
            url = url[:-1]
        return url

    @property
    def portal_help_url(self):
        return '%s/AirWatch/HelpSystem/en/Default.htm' % self.portal_url

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

    def activate(self, user, *args, **kw):
        service_user = self.get_service_user(user)
        if service_user is None:
            service_user = self.register(user)

        try:
            title = '%s - Welcome to Airwatch' % settings.SITE.get('name')
            service_user.activate()
            template_parameters = {
                'user': user,
                'service': self,
                'site': settings.SITE
            }
            text_msg = render_to_string(
                'provisioning/mail/text/activation_airwatch.tmpl.txt', template_parameters
                )
            html_msg = render_to_string(
                'provisioning/mail/html/activation_airwatch.tmpl.html', template_parameters
                )

            send_mail(
                title,
                text_msg,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_msg
            )
        except airwatch.user.UserAlreadyActivatedError:
            pass

    def deactivate(self, user):
        log.debug('Deactivating user %s on Airwatch' % user)
        client = self.get_client()
        service_user = airwatch.user.User.get_remote(client, user.username)
        if service_user is not None:
            service_user.deactivate()

    def assign(self, software, user):
        if self.type not in software.supported_platforms: return

        log.debug('Assigning %s to %s on Airwatch' % (software, user))
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=software)
        service_user = self.get_service_user(user)
        try:
            service_user.add_to_group(metadata.get('group_id'))
        except airwatch.user.UserAlreadyEnrolledError:
            pass

    def unassign(self, software, user):
        if self.type not in software.supported_platforms: return

        log.debug('Removing %s from %s on Airwatch' % (software, user))
        metadata, _ = self.tenantserviceasset_set.get_or_create(asset=software)
        service_user = self.get_service_user(user)
        try:
            service_user.remove_from_group(metadata.get('group_id'))
        except airwatch.user.UserNotEnrolledError:
            pass

    @classmethod
    def get_serializer_data(cls, **data):
        return {
            'username': data.get('username'),
            'password': data.get('password'),
            'server_url': data.get('server_url'),
            'group_id': data.get('group_id')
            }

    class Meta:
        verbose_name = 'AirWatch'


class MobileIron(TenantService, Provisionable):
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


if not getattr(settings, 'PROVISIONABLE_SERVICES'):
    settings.PROVISIONABLE_SERVICES = [
        '.'.join([__name__, k.__name__]) for k in [Okta, AirWatch, MobileIron]
    ]


if not getattr(settings, 'ASSET_CLASSES', []):
    settings.ASSET_CLASSES = [
        '.'.join([__name__, k.__name__]) for k in [Software, Device, MobileDataPlan]
    ]
