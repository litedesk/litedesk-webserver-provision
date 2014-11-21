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
from provisioning import models
from optparse import make_option


class Command(BaseCommand):
    help = 'Updates the last seen timestamp for provisioned services.'
    option_list = BaseCommand.option_list + (
        make_option('--tenant',
            default=1,
            help='Tenant id to do this for. Default=1'),
        )

    def handle(self, *args, **options):
        tenant = models.Tenant.objects.get(pk=options['tenant'])

        self.stdout.write("Get Okta users from Okta.")
        okta = models.Okta.objects.get(tenant = options['tenant'])
        okta_user = okta.get_users()

        user_dict = {}
        for user in okta_user:
            self.stdout.write('%s - %s' % (user['profile']['login'], user['lastLogin']))
            user_dict[user['profile']['login']] = user['lastLogin']

        self.stdout.write("")
        self.stdout.write("Get provisioned Okta services.")
        platform_items = models.UserPlatform.objects.filter(user__tenant = options['tenant']).filter()

        #Update Okta login
        for okta in platform_items:
            if (okta.platform.__subclass__.name == 'Okta'):
                okta_username = '%s@%s' % (okta.user.username, tenant.email_domain)
                self.stdout.write(okta_username)
                if okta_username in user_dict:
                    self.stdout.write("Found")