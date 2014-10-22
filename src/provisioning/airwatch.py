#!/usr/bin/env python

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

from cross7.lib.airwatch.user import User


class Client(object):
    def __init__(self, server_url, username, password, api_token):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.api_token = api_token

    def add_user_to_group(self, user, group_id):
        return User.assign_group(
            self.server_url, self.username, self.password, self.api_token, user.id, group_id
            )

    def activate_user(self, user):
        pass
