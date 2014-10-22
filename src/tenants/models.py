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

import importlib

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.defaultfilters import slugify
from model_utils import Choices
from model_utils.fields import StatusField
from model_utils.models import TimeStampedModel, TimeFramedModel
from model_utils.managers import InheritanceManager, QueryManager

from cross7.lib.active_directory.connection import Connection
from cross7.lib.active_directory.classes.base import Company, User as ActiveDirectoryUser
from audit.models import Trackable, AuditLogEntry, UntrackableChangeError
from syncremote.models import Synchronizable


if not hasattr(settings, 'PROVISIONABLE_SERVICES'):
    settings.PROVISIONABLE_SERVICES = []


class ServiceMeta(object):
    def __init__(self, class_path_string):
        module_name, class_name = class_path_string.rsplit('.', 1)
        module = importlib.import_module(module_name)
        klass = getattr(module, class_name)
        self.model_class = klass
        self.meta = klass._meta

    @property
    def slug(self):
        return self.model_class.service_slug()

    @property
    def name(self):
        return self.meta.verbose_name

    @property
    def model(self):
        return self.model_class


class ActiveDirectory(models.Model):
    url = models.CharField(max_length=300)
    domain = models.CharField(max_length=200)
    ou = models.CharField(max_length=200)
    username = models.CharField(max_length=80)
    password = models.CharField(max_length=1000)

    @property
    def full_url(self):
        return 'ldap://%s' % self.url

    @property
    def dn(self):
        params = ['DC=%s' % component for component in self.url.split('.')]
        params.insert(0, 'cn=Users')
        params.insert(0, 'cn=%s' % self.username)
        return ','.join(params)

    def make_connection(self):
        return Connection(self.full_url, self.dn, self.password)

    def find_company(self, connection):
        try:
            query_results = Company.search(connection, query='(ou=%s)' % self.ou)
            return query_results[0]
        except IndexError:
            return None

    def __unicode__(self):
        return '%s/%s (%s)' % (self.full_url, self.domain, self.ou)


class Tenant(TimeStampedModel):
    name = models.CharField(max_length=1000, unique=True, db_index=True)
    active = models.BooleanField(default=True)
    primary_contact = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='tenant')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='peers', blank=True)
    active_directory = models.OneToOneField(ActiveDirectory, null=True, blank=True)

    #
    email_domain = models.CharField(max_length=300, default='onmicrosoft.com')

    def get_active_directory_connection(self):
        return self.active_directory.make_connection()

    def get_service(self, service_slug):
        services = self.tenantservice_set.select_subclasses()
        try:
            return [s for s in services if s.service_slug() == service_slug].pop()
        except IndexError:
            return None

    def __unicode__(self):
        return self.name


class TenantItem(models.Model):
    tenant = models.ForeignKey(Tenant)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    item = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return 'Item %s from %s' % (self.item, self.tenant)


class TenantService(models.Model):
    PLATFORM_TYPE_CHOICES = Choices('mobile', 'web', 'windows')
    PLATFORM_TYPES = [p[0] for p in PLATFORM_TYPE_CHOICES]
    ACTIVE_DIRECTORY_CONTROLLER = False

    objects = InheritanceManager()
    active = QueryManager(is_active=True)
    tenant = models.ForeignKey(Tenant)
    is_active = models.BooleanField(default=True)
    api_token = models.CharField(max_length=128)

    @property
    def service(self):
        return self.__class__.service_slug()

    @property
    def type(self):
        return self.__class__.PLATFORM_TYPE

    @property
    def name(self):
        return self._meta.verbose_name

    @property
    def is_active_directory_controller(self):
        return self.ACTIVE_DIRECTORY_CONTROLLER

    def register(self, user):
        raise NotImplementedError

    def activate(self, user):
        pass

    def get_service_user(self, user):
        raise NotImplementedError

    def validate_unique(self, exclude=None):
        tenant_services = self.tenant.tenantservice_set.select_subclasses()
        if self.pk is not None:
            tenant_services = tenant_services.exclude(pk=self.pk)

        active_services = tenant_services.filter(is_active=True)
        if self.is_active and self.type in [s.type for s in active_services]:
            raise ValidationError('Active %s service already exists' % self.type)

        super(TenantService, self).validate_unique(exclude=None)

    def __unicode__(self):
        subclassed = TenantService.objects.get_subclass(id=self.id)
        return '%s service for %s' % (subclassed.name, self.tenant)

    @classmethod
    def get_serializer_data(self, **data):
        return {}

    @classmethod
    def service_slug(cls):
        return slugify(cls._meta.verbose_name)

    @classmethod
    def make(cls, tenant, api_token, active, *args, **kw):
        return cls(
            tenant=tenant,
            api_token=api_token,
            is_active=active,
            **cls.get_serializer_data(**kw)
            )

    @staticmethod
    def on_user_creation(*args, **kw):
        if kw.get('created'):
            user = kw.get('instance')
            for service in user.tenant.tenantservice_set.select_subclasses():
                if service.is_active_directory_controller:
                    service.register(user)

    @staticmethod
    def get_available():
        return [ServiceMeta(s) for s in settings.PROVISIONABLE_SERVICES]


class User(Trackable, Synchronizable):
    TRACKABLE_ATTRIBUTES = ['first_name', 'last_name', 'status']
    STATUS = Choices('staged', 'pending', 'active', 'suspended', 'disabled')

    tenant = models.ForeignKey(Tenant)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    display_name = models.CharField(max_length=200, null=True)
    mobile_phone_number = models.CharField(max_length=16, null=True, blank=True)
    username = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    status = StatusField()

    @property
    def tenant_email(self):
        return '%s@%s' % (self.username, self.tenant.email_domain)

    def push(self):
        with self.tenant.get_active_directory_connection() as connection:
            user = ActiveDirectoryUser(
                connection,
                parent=self.tenant.active_directory.find_company(connection),
                given_name=self.first_name,
                sn=self.last_name,
                s_am_account_name=self.username,
                mail=self.email,
                display_name=self.display_name or self.get_default_display_name(),
                user_principal_name=self.tenant_email
                )
            user.save()

    def pull(self):
        pass

    def get_default_display_name(self):
        return ' '.join([self.first_name, self.last_name])

    def save(self, *args, **kw):
        with transaction.atomic():
            super(User, self).save(*args, **kw)
            self.sync(force_push=kw.get('force_insert'))

    def __unicode__(self):
        return self.username

    class Meta:
        unique_together = ('tenant', 'username')


class UserProvisionable(Trackable, TimeFramedModel):
    TRACKABLE_ATTRIBUTES = ['user', 'start', 'end']

    user = models.ForeignKey(User)

    @property
    def tenant(self):
        return self.user.tenant

    @property
    def provisioned(self):
        return self.start is not None and self.end is None

    def save(self, editor=None, *args, **kw):
        if editor is None:
            raise UntrackableChangeError('No user responsible for provision change')

        with transaction.atomic():
            models.Model.save(self, *args, **kw)
            AuditLogEntry.objects.create(
                edited_by=editor,
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.id,
                data=self._trackable_attributes
            )

    class Meta:
        abstract = True


class UserGroup(models.Model):
    tenant = models.ForeignKey(Tenant)
    name = models.CharField(max_length=80)
    members = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        return '%s@%s' % (self.name, self.tenant.name)

    class Meta:
        unique_together = ('name', 'tenant')


# Signals
post_save.connect(TenantService.on_user_creation, dispatch_uid='user_add', sender=User)
