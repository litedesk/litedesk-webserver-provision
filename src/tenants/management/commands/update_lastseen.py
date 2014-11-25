#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014, Deutsche Telekom AG - Laboratories (T-Labs)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from django.core.management.base import BaseCommand
from provisioning import models
from optparse import make_option
from oauth2client.client import SignedJwtAssertionCredentials
import httplib2
from apiclient import errors
from apiclient.discovery import build
from dateutil import parser


class Command(BaseCommand):
    # Check
    # https://developers.google.com/admin-sdk/directory/v1/guides/authorizing
    # for all available scopes
    OAUTH_SCOPE = ['https://www.googleapis.com/auth/admin.directory.user',
                   'https://www.googleapis.com/auth/admin.directory.device.chromeos']

    help = 'Updates the last seen timestamp for provisioned services.'
    option_list = BaseCommand.option_list + (
        make_option('--skip-okta',
                    action='store_true',
                    dest='skip-okta',
                    default=False,
                    help='Do not query Okta. Default=False'),
        make_option('--skip-google',
                    action='store_true',
                    dest='skip-google',
                    default=False,
                    help='Do not query Google. Default=False'),
        make_option('--skip-airwatch',
                    action='store_true',
                    dest='skip-airwatch',
                    default=False,
                    help='Do not query AirWatch. Default=False'),
        make_option('--tenant',
                    dest='tenant',
                    default=1,
                    help='Tenant id to do this for. Default=1'),
    )

    def handle(self, *args, **options):
        tenant = models.Tenant.objects.get(pk=options['tenant'])
        okta_item = models.Okta.objects.get(tenant=tenant)
        users = okta_item.userplatform_set.all()
        self.stdout.write("Okta users in database.")
        user_dict = {}
        for user in users:
            username = '%s@%s' % (user.user.username, tenant.email_domain)
            user_dict[username] = {'username': user.user.username}
            self.stdout.write(username)

        if not options['skip-okta']:
            self.stdout.write("")
            self.stdout.write("Get Okta user logins.")
            okta_service = models.Okta.objects.get(tenant=options['tenant'])
            okta_users = okta_service.get_users()

            for okta_user in okta_users:
                self.stdout.write(
                    '%s - %s' % (okta_user['profile']
                                 ['login'], okta_user['lastLogin']),
                    ending='')
                if okta_user['profile']['login'] in user_dict:
                    self.stdout.write(' SAVE')
                    user_dict[okta_user['profile']['login']].update({
                        'okta_last_login': okta_user['lastLogin'],
                        'okta_id': okta_user['id']})
                else:
                    self.stdout.write('')

            # Update Okta login
            # for it in okta_provisionables:
            #     it_username = '%s@%s' % (it.user.username, tenant.email_domain)
            #     if it_username in user_dict:
            #         self.stdout.write('%s Okta -> %s' %
            #                           (it_username, user_dict[it_username]['last_login']))

            # Get Okta application SSO events
            self.stdout.write("")
            self.stdout.write("Get Okta SSO events.")
            okta_client = okta_service.get_client()

            usersoftwares = models.UserSoftware.objects.filter(
                user__tenant=tenant)
            for usersoftware in usersoftwares:
                oktatenantservice = usersoftware.software.tenantserviceasset_set.get(
                    service=okta_service)
                event = okta_client.last_sso_event(
                    user_dict[usersoftware.user.tenant_email]['okta_id'],
                    oktatenantservice.get('application_id'))
                self.stdout.write(
                    '%s - %s -> %s' % (usersoftware.user.tenant_email,
                                       usersoftware.software, event['published']))

        if not options['skip-google']:
            # Get Google lastseen
            google_tenant_asset = tenant.tenantasset_set.get(
                asset__name='Google Account')

            # Run through the OAuth flow and retrieve credentials
            with open(google_tenant_asset.get('CERTIFICATE_FILE_PATH')) as f:
                private_key = f.read()
            credentials = SignedJwtAssertionCredentials(
                google_tenant_asset.get('CLIENT_EMAIL'),
                private_key,
                scope=self.OAUTH_SCOPE,
                sub=google_tenant_asset.get('ADMINISTRATOR')
            )

            # Create an httplib2.Http object and authorize it with our
            # credentials
            http = httplib2.Http()
            http = credentials.authorize(http)
            directory_service = build('admin', 'directory_v1', http=http)

            # Get Google Account lastseen information
            all_users = []
            page_token = None
            params = {'customer': 'my_customer'}

            self.stdout.write("")
            self.stdout.write("Get Google Account users")
            while True:
                try:
                    if page_token:
                        params['pageToken'] = page_token
                    current_page = directory_service.users().list(
                        **params).execute()

                    all_users.extend(current_page['users'])
                    page_token = current_page.get('nextPageToken')
                    if not page_token:
                        break
                except errors.HttpError as error:
                    self.stderr.write('An error occurred: %s' % error)
                    break

            for user in all_users:
                self.stdout.write(
                    user['primaryEmail'] + " - " + user['lastLoginTime'])

            # Get Google Device lastseen information
            all_devices = []
            page_token = None
            params = {'customerId': 'my_customer'}

            while True:
                try:
                    if page_token:
                        params['pageToken'] = page_token
                    current_page = directory_service.chromeosdevices().list(
                        **params).execute()
                    all_devices.extend(current_page['chromeosdevices'])
                    page_token = current_page.get('nextPageToken')
                    if not page_token:
                        break
                except errors.HttpError as error:
                    self.stderr.write('An error occurred: %s' % error)
                    break

            self.stdout.write("")
            self.stdout.write("Get Google Devices")
            for device in all_devices:
                # self.stdout.write(
                #     '%s - %s -> %s' %
                # (device['recentUsers'][0]['email']
                #    if device.has_key('recentUsers') else 'never used',
                #                        device['serialNumber'],
                #                        device['lastSync']))
                self.stdout.write('%s - %s -> %s' % (device['annotatedUser'],
                                                     device['serialNumber'],
                                                     device['lastSync']))

        if not options['skip-airwatch']:
            self.stdout.write("")
            self.stdout.write("Get AirWatch Devices & Platform usage")

            airwatch_item = models.AirWatch.objects.get(tenant=tenant)
            airwatch_client = airwatch_item.get_client()
            endpoint = 'mdm/devices/search'

            for user in user_dict:
                response = airwatch_client.call_api(
                    'GET', endpoint, params={'user': user_dict[user]['username']})
                response.raise_for_status()
                if response.status_code == 200:
                    devices = response.json().get('Devices')
                    newest_seen = parser.parse(devices[0]['LastSeen'])
                    for device in devices:
                        seen = parser.parse(device['LastSeen'])
                        if seen > newest_seen:
                            newest_seen = seen
                        self.stdout.write("%s - %s -> %s" % (user, device['SerialNumber'], device['LastSeen']))
                    self.stdout.write("%s -> %s" % (user, newest_seen))