#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

def register_user_in_provisioning_service(service, user):
    # FIXME: The delay is necessary to avoid that services which depend on AD can get to see the newly created user
    time.sleep(4)
    service.register(user)
