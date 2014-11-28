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

import httplib2
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials
import os
from django.conf import settings


class Client(object):

    OAUTH_SCOPE = ['https://www.googleapis.com/auth/admin.directory.user',
                   'https://www.googleapis.com/auth/admin.directory.device.chromeos']

    def __init__(self, tenant):
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
        self.directory_service = build('admin', 'directory_v1', http=http)

    def get_devices(self):
        all_devices = []
        page_token = None
        params = {'customerId': 'my_customer'}

        while True:
            try:
                if page_token:
                    params['pageToken'] = page_token
                current_page = self.directory_service.chromeosdevices().list(
                    **params).execute()
                all_devices.extend(current_page['chromeosdevices'])
                page_token = current_page.get('nextPageToken')
                if not page_token:
                    break
            except errors.HttpError as error:
                self.stderr.write('An error occurred: %s' % error)
                break

        return all_devices
