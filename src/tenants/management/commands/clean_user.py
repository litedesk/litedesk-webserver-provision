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

import sys
import logging

from django.contrib.auth.models import User as DjangoUser
from django.core.management.base import BaseCommand
from optparse import make_option
from tenants.models import User


log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Unassigns all assets from a user.'
    option_list = BaseCommand.option_list + (
        make_option('--username', dest='user', help='Username of target user'),
        )

    def handle(self, *args, **options):
        username = options.get('user')

        if not username:
            sys.exit('Username not provided')

        user = User.objects.get(username=username)
        editor = DjangoUser.objects.filter(is_superuser=True)[0]

        for up in list(user.userprovisionable_set.all()):
            service = up.service.__subclassed__
            log.info('Deprovisioning %s on %s' % (up.item, service))
            up.item.deprovision(service, user, editor=editor)

        for service in user.services.select_subclasses():
            service.deactivate(user)
