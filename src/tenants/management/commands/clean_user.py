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
from tenants.models import User
import json


class Command(BaseCommand):
    help = 'anasigns all assests from a the username.'
    option_list = BaseCommand.option_list + (
        make_option('--username',
                    default="bruce.wayne",
                    help='Username to find. Default="bruce.wayne"'),
        )

    # TODO: change this when raphael finishes with his refactoring
    def handle(self, *args, **options):
        user = User.objects.filter(username=options["username"]).get()
        editor = user.tenant.primary_contact
        for us in user.software.current():
            us.deprovision(editor=editor)
        self.stdout.write("user is now clean")


