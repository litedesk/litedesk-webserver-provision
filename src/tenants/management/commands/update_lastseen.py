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
import datetime
import pytz
from django.contrib.contenttypes.models import ContentType


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

    def _parseDateTime(self, stamp):
        parsed = parser.parse(stamp)
        utc = parsed.astimezone(pytz.utc)
        stripped = utc.replace(tzinfo=None)
        return stripped

    def handle(self, *args, **options):
        tenant = models.Tenant.objects.get(pk=options['tenant'])
        okta_item = models.Okta.objects.get(tenant=tenant)
        users = models.User.objects.filter(services=okta_item)
        software_contenttype = ContentType.objects.get_for_model(
            models.Software)
        google_software = models.Software.objects.get(name='Google Account')
        device_contenttype = ContentType.objects.get_for_model(
            models.Device)

        self.stdout.write("Okta users in database.")
        user_dict = {}
        for user in users:
            username = '%s@%s' % (user.username, tenant.email_domain)
            user_dict[username] = {'username': user.username, 'user': user}
            self.stdout.write(username)

        if not options['skip-okta']:
            self.stdout.write("")
            self.stdout.write("Get Okta user logins.")

            okta_users = okta_item.get_users()
            okta_item_type = ContentType.objects.get_for_model(okta_item)
            for okta_user in okta_users:
                okta_username = okta_user['profile']['login']
                if okta_username in user_dict:
                    user_dict[okta_username].update(
                        {'okta_id': okta_user['id']})
                    if okta_user['lastLogin']:
                        models.LastSeenEvent.objects.create(
                            user=user_dict[okta_username]['user'],
                            item_type=okta_item_type,
                            object_id=okta_item.id,
                            last_seen=self._parseDateTime(okta_user['lastLogin']))
                        self.stdout.write(
                            '%s - %s' % (okta_username, okta_user['lastLogin']))

            # Get Okta application SSO events
            self.stdout.write("")
            self.stdout.write("Get Okta SSO events.")
            okta_client = okta_item.get_client()

            usersoftwares = models.UserProvisionable.objects.filter(
                user__tenant=tenant,
                item_type=software_contenttype,
                service=okta_item).exclude(
                object_id=google_software.id)
                # Google accoint login is done below directly from google
            for usersoftware in usersoftwares:
                oktatenantservice = usersoftware.item.tenantserviceasset_set.get(
                    service=okta_item)
                event = okta_client.last_sso_event(
                    user_dict[usersoftware.user.tenant_email]['okta_id'],
                    oktatenantservice.get('application_id'))
                if event:
                    models.LastSeenEvent.objects.create(
                        user=usersoftware.user,
                        item_type=software_contenttype,
                        object_id=usersoftware.object_id,
                        last_seen=self._parseDateTime(event['published']))
                    self.stdout.write(
                        '%s - %s -> %s' % (usersoftware.user.tenant_email,
                                           usersoftware.item.name,
                                           event and event['published'] or "never"))

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
                if user['lastLoginTime'] == '1970-01-01T00:00:00.000Z':
                    continue
                if models.UserProvisionable.objects.filter(
                        user__username=user['primaryEmail'].split('@')[0],
                        user__tenant=tenant,
                        item_type=software_contenttype,
                        object_id=google_software.id).exists():
                    models.LastSeenEvent.objects.create(
                        user=user_dict[user['primaryEmail']]['user'],
                        item_type=software_contenttype,
                        object_id=google_software.id,
                        last_seen=self._parseDateTime(user['lastLoginTime']))
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
            chromebook_device = models.Device.objects.get(name='Chromebook')
            for device in all_devices:
                if models.UserProvisionable.objects.filter(
                        user__username=device['annotatedUser'].split('@')[0],
                        user__tenant=tenant,
                        item_type=device_contenttype,
                        object_id=chromebook_device.id).exists():
                    models.LastSeenEvent.objects.create(
                        user=user_dict[device['annotatedUser']]['user'],
                        item_type=device_contenttype,
                        object_id=chromebook_device.id,
                        last_seen=self._parseDateTime(device['lastSync']))
                    self.stdout.write('%s - %s -> %s' % (device['annotatedUser'],
                                                         device[
                                                             'serialNumber'],
                                                         device['lastSync']))

        if not options['skip-airwatch']:
            self.stdout.write("")
            self.stdout.write("Get AirWatch Devices & Platform usage")

            airwatch_item = models.AirWatch.objects.get(tenant=tenant)
            airwatch_client = airwatch_item.get_client()
            endpoint = 'mdm/devices/search'

            iPad_device = models.Device.objects.get(name='iPad')
            iPhone_device = models.Device.objects.get(name='iPhone')
            airwatch_item_type = ContentType.objects.get_for_model(airwatch_item)

            airwatch_users = models.User.objects.filter(services=airwatch_item)
            for user in airwatch_users:
                response = airwatch_client.call_api(
                    'GET', endpoint, params={'user': user.username})
                response.raise_for_status()
                if response.status_code == 200:
                    devices = response.json().get('Devices')
                    newest_seen = parser.parse(devices[0]['LastSeen'])
                    for device in devices:
                        seen = parser.parse(device['LastSeen'])
                        if seen > newest_seen:
                            newest_seen = seen
                        if device['Model'].startswith(iPad_device.name):
                            device_item = iPad_device
                        elif device['Model'].startswith(iPhone_device.name):
                            device_item = iPhone_device
                        else:
                            device_item = None
                        models.LastSeenEvent.objects.create(
                            user=user,
                            item_type=device_contenttype,
                            object_id=device_item.id,
                            last_seen=seen)
                        self.stdout.write(
                            "%s - %s -> %s" % (user, device['SerialNumber'],
                                               device['LastSeen']))
                    self.stdout.write("%s -> %s" % (user, newest_seen))
                    models.LastSeenEvent.objects.create(
                        user=user,
                        item_type=airwatch_item_type,
                        object_id=airwatch_item.id,
                        last_seen=newest_seen)
