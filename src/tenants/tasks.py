#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time


log = logging.getLogger(__name__)


def register_user_in_provisioning_service(service, user):
    # FIXME: The delay is necessary to avoid that services
    # which depend on AD can get to see the newly created user
    time.sleep(4)
    try:
        service.register(user)
    except Exception, why:
        log.warn('Failed when registering user %s on %s: %s' % (user, service, why))
