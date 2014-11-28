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
import os
from django.conf import settings


class Command(BaseCommand):
    # Check
    # https://developers.google.com/admin-sdk/directory/v1/guides/authorizing
    # for all available scopes
    OAUTH_SCOPE = ['https://www.googleapis.com/auth/admin.directory.user',
                   'https://www.googleapis.com/auth/admin.directory.device.chromeos']

    help = 'Updates the last seen timestamp for provisioned services.'
    option_list = BaseCommand.option_list + (
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
        # Get Google lastseen
        google_tenant_asset = tenant.tenantasset_set.get(
            asset__name='Google Account')
        certificate_file_path = os.path.join(
            settings.CERTIFICATES_DIR, google_tenant_asset.get('CERTIFICATE_FILE_NAME')
        )
        # Run through the OAuth flow and retrieve credentials
        with open(certificate_file_path) as f:
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
            self.stdout.write('%s - %s -> %s' % (device['annotatedUser'],
                                                 device['serialNumber'],
                                                 device['lastSync']))

        self.stdout.write("")
        self.stdout.write("Get AirWatch Devices & Platform usage")

        airwatch_item = models.AirWatch.objects.get(tenant=tenant)
        devices = airwatch_item.get_avilable_devices()
        for device in devices:
            self.stdout.write('%s (%s) user: %s' %
                              (device['Model'], device['SerialNumber'], device['UserName']))
