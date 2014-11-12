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

import logging


log = logging.getLogger(__name__)


def run_provisioning_for_user(user, editor=None):
    log.debug('Running provisioning for %s' % user)
    for user_platform in user.platforms.current():
        if not user_platform.is_provisionable:
            log.debug('Platform %s has been already deprovisioned' % user_platform.platform)
            continue

        # platforms will be a TenantService object. We need the subclass.
        platform = user_platform.platform.__subclass__
        log.debug('Is active on platform %s? %s' % (platform, user_platform.is_active))
        if not user_platform.is_active:
            user_platform.activate(editor=editor)

        for user_software in user.software.current():
            log.info('Assigning software %s for %s' % (user_software.software, user))
            platform.assign(user_software.software, user)
