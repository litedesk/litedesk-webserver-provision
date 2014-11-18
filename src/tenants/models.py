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
import importlib
import datetime

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
from model_utils.models import TimeStampedModel
from model_utils.managers import InheritanceManager, QueryManager

from litedesk.lib.active_directory.session import Session
from litedesk.lib.active_directory.classes.base import Company, User as ActiveDirectoryUser
from audit.models import Trackable, UntrackableChangeError
from syncremote.models import Synchronizable

import tasks

log = logging.getLogger(__name__)


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
        return 'ldaps://%s' % self.url

    @property
    def dn(self):
        params = ['DC=%s' % component for component in self.url.split('.')]
        params.insert(0, 'cn=Users')
        params.insert(0, 'cn=%s' % self.username)
        return ','.join(params)

    def make_session(self):
        return Session(self.full_url, self.dn, self.password, True)

    def find_company(self):
        session = self.make_session()
        try:
            query_results = Company.search(session, query='(ou=%s)' % self.ou)
            return query_results[0]
        except IndexError:
            return None

    def find_user(self, username):
        try:
            session = self.make_session()
            query_results = Company.search(session, query='(ou=%s)' % self.ou)
            company = query_results[0]
            return [u for u in company.users if u.s_am_account_name == username].pop()
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

    def get_active_directory_session(self):
        return self.active_directory.make_session()

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
    def __subclass__(self):
        return TenantService.objects.get_subclass(id=self.id)

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
                    tasks.register_user_in_provisioning_service(service, user)

    @staticmethod
    def get_available():
        return [ServiceMeta(s) for s in settings.PROVISIONABLE_SERVICES]


class User(Trackable, Synchronizable):
    TRACKABLE_ATTRIBUTES = ['first_name', 'last_name', 'status', 'email']
    SYNCHRONIZABLE_ATTRIBUTES_MAP = {
            'username': 's_am_account_name',
            'first_name': 'given_name',
            'last_name': 'sn',
            'email': 'mail',
            'display_name': 'display_name'
        }
    STATUS = Choices('staged', 'pending', 'active', 'suspended', 'disabled')

    tenant = models.ForeignKey(Tenant)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    display_name = models.CharField(max_length=200, null=True)
    mobile_phone_number = models.CharField(max_length=16, null=True, blank=True)
    username = models.CharField(max_length=100, editable=False)
    email = models.EmailField(null=True)
    status = StatusField()

    @property
    def tenant_email(self):
        return '%s@%s' % (self.username, self.tenant.email_domain)

    @property
    def full_username(self):
        return '%s@%s' % (self.username, self.tenant.active_directory.url)

    def get_remote(self):
        return self.tenant.active_directory.find_user(self.username)

    def push(self):
        log.info('Pushing user %s' % self)
        with transaction.atomic():
            remote_user = self.get_remote()
            session = self.tenant.get_active_directory_session()
            if remote_user is None:
                remote_user = ActiveDirectoryUser(
                    session,
                    parent=self.tenant.active_directory.find_company(),
                    given_name=self.first_name,
                    sn=self.last_name,
                    s_am_account_name=self.username,
                    mail=self.email,
                    display_name=self.display_name or self.get_default_display_name(),
                    user_principal_name=self.full_username
                    )
            else:
                remote_user.mail = self.email
                remote_user.display_name = self.display_name
                remote_user.given_name = self.first_name
                remote_user.sn = self.last_name
            remote_user.save()

    def pull(self):
        pass

    def get_default_display_name(self):
        return ' '.join([self.first_name, self.last_name])

    def save(self, *args, **kw):
        with transaction.atomic():
            self.sync(force_push=kw.get('force_insert'))
            super(User, self).save(*args, **kw)

    def __unicode__(self):
        return self.username

    @classmethod
    def load(cls, remote_object, **kw):
        editor = kw.pop('editor', None)

        if editor is None:
            raise UntrackableChangeError('Can not load new data without tracking editor')

        try:
            editor_tenant = editor.tenant
        except:
            editor_tenant = None

        tenant = kw.pop('tenant', editor_tenant)
        if tenant is None:
            raise ValueError('User %s has no tenant' % remote_object)

        obj = cls(
            username=remote_object.s_am_account_name,
            tenant=tenant,
            first_name=remote_object.given_name,
            last_name=remote_object.sn,
            email=remote_object.mail,
            display_name=remote_object.display_name,
            last_remote_read=datetime.datetime.now()
            )

        obj.save(editor=editor)

    @classmethod
    def get_remote_last_modified(cls, remote_object):
        return datetime.datetime.strptime(remote_object.when_changed, '%Y%m%d%H%M%S.%fZ')

    class Meta:
        unique_together = ('tenant', 'username')


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
