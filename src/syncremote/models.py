#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from django.db import models


class Synchronizable(models.Model):
    SYNCHRONIZABLE_ATTRIBUTES_MAP = {}

    last_remote_read = models.DateTimeField(null=True, editable=False)
    last_remote_save = models.DateTimeField(null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False)

    @property
    def last_sync(self):
        if self.last_remote_read is not None and self.last_remote_save is not None:
            return max(self.last_remote_read, self.last_remote_save)

        if self.last_remote_save is not None:
            return self.last_remote_save

        if self.last_remote_read is not None:
            return self.last_remote_read

        return None

    def _needs_pull(self, remote_object):
        if self.last_remote_read is None: return True
        return self.last_remote_read < self.__class__.get_remote_last_modified(remote_object)

    def _needs_push(self, remote_object):
        if self.last_remote_save is None: return True
        return self.last_modified > self.__class__.get_remote_last_modified(remote_object)

    @property
    def _has_remote_save(self):
        return self.last_remote_save is not None

    def sync(self, force_push=False, force_pull=False):
        remote = self.get_remote()
        changed = (self._get_changed_attributes(remote_object=remote) != [])
        needs_pull = changed and self._needs_pull(remote)
        needs_push = changed and self._needs_push(remote)

        if force_pull or needs_pull:
            self.pull()
            self.last_remote_read = datetime.datetime.now()

        if force_push or needs_push:
            self.push()
            self.last_remote_save = datetime.datetime.now()

    def _get_changed_attributes(self, remote_object=None):
        remote = remote_object or self.get_remote()
        if remote is None: return self.SYNCHRONIZABLE_ATTRIBUTES_MAP.keys()
        return [
            local_attr
            for local_attr, remote_attr in self.SYNCHRONIZABLE_ATTRIBUTES_MAP.items()
            if getattr(self, local_attr) != getattr(remote, remote_attr)
            ]

    def get_remote(self):
        raise NotImplementedError

    def pull(self):
        raise NotImplementedError

    def push(self):
        raise NotImplementedError

    @classmethod
    def get_remote_last_modified(cls, remote_object):
        raise NotImplementedError

    @classmethod
    def load(cls, remote_object, **kw):
        raise NotImplementedError

    @classmethod
    def merge(cls, local_object, remote_object, **extra_fields):
        remote_last_modified = local_object.get_remote_last_modified(remote_object)
        if local_object.last_modified > remote_last_modified: return
        for local_attr, remote_attr in local_object.SYNCHRONIZABLE_ATTRIBUTES_MAP.items():

            remote_value = getattr(remote_object, remote_attr)
            setattr(local_object, local_attr, remote_value)

        local_object.save(**extra_fields)

    class Meta:
        abstract = True
