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


from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from litedesk.lib.active_directory.classes.base import Company

from tenants import models


class Command(BaseCommand):
    help = 'For all tenants with AD credentials, load the user table'

    def handle(self, *fixture_labels, **options):
        user_class = get_user_model()
        admin = user_class.objects.filter(is_superuser=True)[0]
        for ad in models.ActiveDirectory.objects.all():
            session = ad.make_session()
            for company in Company.search(session, query='(ou=%s)' % ad.ou):
                for remote_user in company.users:
                    username = remote_user.s_am_account_name
                    local_user = models.User.objects.filter(username=username)
                    if local_user.exists():
                        models.User.merge(local_user.get(), remote_user, editor=admin)
                    else:
                        models.User.load(remote_user, editor=admin, tenant=ad.tenant)
