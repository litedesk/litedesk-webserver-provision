#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from django.db import models


class Synchronizable(models.Model):
    SYNCHRONIZABLE_ATTRIBUTES_MAP = {}

    last_synced_at = models.DateTimeField(null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, editable=False)

    @property
    def synced(self):
        if self.last_modified is None or self.last_synced_at is None:
            return False

        return self.last_modified < self.last_synced_at

    @property
    def needs_push(self):
         # object was created in the client
        if self.pk is None: return True

         # We never synced
        if self.last_synced_at is None: return True

        return self.last_modified > self.last_synced_at

    @property
    def needs_pull(self):
        if self.pk is None: return False
        if self.last_synced_at is None: return True

        return self.last_modified < self.last_synced_at

    def get_remote(self):
        raise NotImplementedError

    def sync(self, force_push=False, force_pull=False):
        def _push():
            self.push()
            self.last_synced_at = datetime.datetime.now()

        def _pull():
            self.pull()
            self.last_synced_at = self.last_modified = datetime.datetime.now()

        if force_push: _push()
        if force_pull: _pull()

        if self.synced: return

        if self.needs_push: _push()
        if self.needs_pull: _pull()

    def pull(self):
        raise NotImplementedError

    def push(self):
        raise NotImplementedError

    class Meta:
        abstract = True
