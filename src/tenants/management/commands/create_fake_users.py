#!/usr/bin/env python
#-*- coding: utf-8 -*-

import random
from optparse import make_option, Values

from django.core.management.base import BaseCommand

from tenants import factories

OPTIONS = (
    make_option('-s', '--size', dest='size', type='int', help='# users', default=1000),
    make_option('-t', '--tenants', dest='tenants', type='int', help='# tenants', default=1)
    )


class Command(BaseCommand):
    help = 'Creates fixtures full of fake user data'

    option_list = BaseCommand.option_list + OPTIONS

    def handle(self, *fixture_labels, **options):
        opts = Values(options)

        tenants = [factories.TenantFactory() for _ in xrange(opts.tenants)]
        for _ in xrange(opts.size):
            factories.UserFactory(tenant=random.choice(tenants))
