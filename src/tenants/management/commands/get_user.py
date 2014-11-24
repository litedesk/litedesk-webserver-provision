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
from optparse import make_option
from provisioning import okta
from provisioning.models import Okta
from litedesk.lib.airwatch import user
# from litedesk.lib.airwatch import groups
from provisioning.models import AirWatch
import json


class Command(BaseCommand):
    help = 'Get information about a user.'
    option_list = BaseCommand.option_list + (
        make_option('--username',
                    default="bruce.wayne",
                    help='Username to find. Default="bruce.wayne"'),
        )

    def handle(self, *args, **options):
        result = {'okta': {}, 'airwatch': {}}
        okta_service = Okta.objects.all().get()
        client = okta.Client(okta_service.domain, okta_service.api_token)
        okta_user = client.search(okta.User, options["username"].split('.')[0])[0]
         # self.stdout.write("got the Okta user with the id")
        result['okta']['id'] = okta_user.id
        result['okta']['status'] = okta_user.status
        result['okta']['applications'] = []
        okta_apps = client.user_applications(okta_user)
        for app in okta_apps:
            result['okta']['applications'].append({"name": app['name'],"status":app['status']})
        airwatch_service = AirWatch.objects.all().get()
        airwatch_client = airwatch_service.get_client()
        airwatch_user = user.User.get_remote(airwatch_client, options["username"])
        # usernames = groups.UserGroups.usernames_by_group_id(
        #    airwatch_client,airwatch_service.airwatch
        #    )
        result['airwatch']['id'] = airwatch_user.id
        result['airwatch']['Status'] = airwatch_user.Status
        self.stdout.write(json.dumps(result))


