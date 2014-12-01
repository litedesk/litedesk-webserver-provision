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
from provisioning.google import Client
# import pprint


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

    def handle(self, *args, **options):
        tenant = models.Tenant.objects.get(pk=options['tenant'])
        google_client = Client(tenant)
        all_devices = google_client.get_available_devices()
        self.stdout.write("")
        self.stdout.write("Get Google Devices")
        for device in all_devices:
            #pp = pprint.PrettyPrinter(indent=4)
            #self.stdout.write(pp.pprint(device))
            self.stdout.write('%s - %s - %s ' % (device['username'],
                                                 device['serial_number'],
                                                 device['model']))

        self.stdout.write("")
        self.stdout.write("Get AirWatch Devices & Platform usage")

        airwatch_item = models.AirWatch.objects.get(tenant=tenant)
        devices = airwatch_item.get_available_devices()
        for device in devices:
            self.stdout.write('%s (%s) user: %s' %
                              (device['model'], device['serial_number'], device['username']))
