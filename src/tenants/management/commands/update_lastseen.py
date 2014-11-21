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
from provisioning import okta
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
        okta_service = models.Okta.objects.get(tenant = options['tenant'])
        okta_user = okta_service.get_users()

        user_dict = {}
        for user in okta_user:
            self.stdout.write('%s - %s' % (user['profile']['login'], user['lastLogin']))
            user_dict[user['profile']['login']] = { 'last_login': user['lastLogin'], 'id': user['id'] }

        self.stdout.write("")
        self.stdout.write("Get provisioned Okta services.")

        #Update Okta login
        okta_item = models.Okta.objects.get(tenant = tenant)
        okta_provisionables = okta_item.userplatform_set.all()
        for it in okta_provisionables:
            it_username = '%s@%s' % (it.user.username, tenant.email_domain)
            if it_username in user_dict:
                self.stdout.write('%s Okta -> %s' % (it_username, user_dict[it_username]['last_login']))

        #Get Okta application SSO events
        self.stdout.write("")
        self.stdout.write("Get Okta SSO events.")
        okta_client = okta_service.get_client()

        usersoftwares = models.UserSoftware.objects.filter(user__tenant = tenant)
        for usersoftware in usersoftwares:
            oktatenantservice = usersoftware.software.tenantserviceasset_set.get(service = okta_service)
            event = okta_client.last_sso_event(user_dict[usersoftware.user.tenant_email]['id'], oktatenantservice.get('application_id'))
            self.stdout.write('%s %s -> %s' % (usersoftware.user.tenant_email, usersoftware.software, event['published']))

