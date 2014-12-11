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

from optparse import make_option, Values
from django.core.management.base import BaseCommand

from tenants.models import User, Tenant
from provisioning.models import Asset


class Command(BaseCommand):
    help = 'Provision assets to users'

    option_list = BaseCommand.option_list + (
        make_option('-u', '--user', dest='user', help='username'),
        make_option('-t', '--tenant', dest='tenant', help='Tenant name'),
        make_option('-a', '--asset', dest='asset', help='Asset key'),
        make_option('-s', '--service', dest='service', help='Service')
        )

    def handle(self, *fixture_labels, **options):
        opts = Values(options)
        tenant = Tenant.objects.get(name=opts.tenant)
        user = User.objects.get(username=opts.user, tenant=tenant)
        service = tenant.get_service(opts.service)
        asset = Asset.objects.get_subclass(slug=opts.asset)
        service.assign(asset, user)
