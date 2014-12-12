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

import time

from django.core.management.base import BaseCommand

from tenants.models import User
from provisioning.models import AirWatch
from litedesk.lib.airwatch.device import Device
from litedesk.lib.airwatch.app import App


class Command(BaseCommand):
    help = 'Airwatch Daemon'

    def handle(self, *fixture_labels, **options):
        while True:
            aw = AirWatch.objects.first()
            client = aw.get_client()
            for user in User.objects.all():
                self.process_user(aw, client, user)
            time.sleep(5)

    def process_user(self, aw, client, user):
        print user
        softwares = user.get_provisioned_items(service=aw)
        print softwares
        app_ids = [
            app_id
            for ts_asset in (
                aw.tenantserviceasset_set.get_or_create(asset=software)
                for software in softwares
            )
            for app_id in ts_asset[0].metadata['app_ids']
        ]
        print app_ids
        for device in Device.search(client, user=aw.get_service_user(user).UserName):
            print device
            self.process_device(aw, client, device, app_ids)

    def process_device(self, aw, client, device, app_ids):
        for app_id in app_ids:
            try:
                print app_id
                app = App.search(client, Id=app_id)[0]
                print app.ApplicationName
                app.install(device)
            except:
                import sys
                print sys.exc_info()

