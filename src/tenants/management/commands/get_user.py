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
import json


class Command(BaseCommand):
    help = 'Get information about a user.'
    option_list = BaseCommand.option_list + (
        make_option('--username',
            default="alastor",
            help='Username to find. Default="alastor"'),
        )

    def handle(self, *args, **options):
        result = {'okta': {}, 'airwatch': {}}
        okta_service = Okta.objects.all().get()
        client = okta.Client(okta_service.domain, okta_service.api_token)
        user = client.search(okta.User, options["username"])[0]
        # self.stdout.write("got the Okta user with the id")
        result['okta']['id'] = user.id
        result['okta']['status'] = user.status
        self.stdout.write(json.dumps(result))
