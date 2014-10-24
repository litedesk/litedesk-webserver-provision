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


from django.core.management.base import BaseCommand

from cross7.lib.active_directory.connection import Connection
from cross7.lib.active_directory.classes.base import Company

from tenants import models


class Command(BaseCommand):
    help = 'For all tenants with AD credentials, load the user table'

    def handle(self, *fixture_labels, **options):

        for ad in models.ActiveDirectory.objects.all():
            url = 'ldap://%s' % ad.url
            dn = ['DC=%s' % component for component in ad.url.split('.')]
            dn.insert(0, 'cn=Users')
            dn.insert(0, 'cn=%s' % ad.username)
            dn = ','.join(dn)
            with Connection(url, dn, ad.password) as connection:
                for company in Company.search(connection, query='(ou=%s)' % ad.ou):
                    for user in company.users:
                        user, created = models.User.objects.get_or_create(
                            tenant=ad.tenant,
                            username=user.s_am_account_name,
                            defaults={
                                'first_name':user.given_name,
                                'last_name': user.sn,
                                'email': user.mail,
                                'display_name': user.display_name
                            })
                        if not created:
                            user.sync()
