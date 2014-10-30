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

import json
import requests


ERROR_RESPONSES = {
    'ALREADY_ACTIVATED': {
        'summary': 'Activation failed because the user is already active',
        'code': 'E0000016'
        },
    'ALREADY_REGISTERED': {
        # FIXME: I still need to get the correct message/error code.
        'summary': 'Activation failed because the user is already active',
        'code': 'E0000016'
        }
    }


def check_for_error(response, key, exception):
    try:
        response.raise_for_status()
    except requests.HTTPError, exc:
        if check_is_known_error_response(response, 'ALREADY_ACTIVATED'):
            raise exception
        else:
            raise exc


def check_is_known_error_response(response, key):
    try:
        known_error_response = ERROR_RESPONSES[key]
        error_response = response.json()
        return all([
            known_error_response['code'] == error_response.get('errorCode'),
            known_error_response['summary'] == error_response.get('errorSummary')
            ])
    except KeyError:
        return False


class ResourceDoesNotExistError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class UserAlreadyActivatedError(Exception):
    pass


class Resource(object):
    def __init__(self, client, *args, **kw):
        self._client = client
        for k, v in kw.items():
            setattr(self, k, v)


class User(Resource):
    ENDPOINT_ROOT = 'users'


class Application(Resource):
    ENDPOINT_ROOT = 'apps'

    def assign(self, user, profile=None):
        url = '%s/%s/users' % (Application.ENDPOINT_ROOT, self.id)
        payload = {
            'id': user.id
            }
        if profile is not None:
            payload['profile'] = profile
        response = self._client._make_request(url, method='POST', data=payload)
        response.raise_for_status()

    def unassign(self, user):
        url = '%s/%s/users/%s' % (Application.ENDPOINT_ROOT, self.id, user.id)
        response = self._client._make_request(url, method='DELETE')
        response.raise_for_status()


class Client(object):
    def __init__(self, domain, api_token):
        self.domain = domain
        self.api_token = api_token
        self._session = requests.Session()
        self._session.headers.update({
            'Accept': 'application/json',
            'Authorization': 'SSWS %s' % self.api_token,
            'Content-Type': 'application/json'
            })

    def _make_request(self, url, method=None, data=None, **kw):
        if data is not None:
            kw['data'] = json.dumps(data)

        full_url = 'https://%s.okta.com/api/v1/%s' % (self.domain, url)

        return {
            'GET': self._session.get,
            'PUT': self._session.put,
            'POST': self._session.post,
            'DELETE': self._session.delete
            }.get(method, self._session.get)(full_url, **kw)

    def search(self, resource_cls, query_string):
        response = self._make_request(resource_cls.ENDPOINT_ROOT, params={'q': query_string})
        response.raise_for_status()
        return [resource_cls(self, **it) for it in response.json()]

    def get(self, resource_cls, resource_id):
        response = self._make_request('/'.join([resource_cls.ENDPOINT_ROOT, resource_id]))
        if response.status_code == 404:
            raise ResourceDoesNotExistError

        response.raise_for_status()
        return resource_cls(self, **response.json())

    def assign_application_to_user(self, application, user, profile=None):
        application.assign_to_user(user, profile=profile)

    def get_users(self):
        response = self._make_request('users')
        response.raise_for_status()
        return response.json()

    def add_user(self, user, activate=True):
        user_profile_data = {
            'firstName': user.first_name,
            'lastName': user.last_name,
            'email': user.email,
            'login': user.tenant_email
        }

        params = {
            'activate': activate
            }

        data = {'profile': user_profile_data}

        response = self._make_request('users', method='POST', params=params, data=data)
        response.raise_for_status()
        check_for_error(response, 'ALREADY_REGISTERED', UserAlreadyExistsError)
        return response.json()

    def activate_user(self, user, send_email=True):
        if getattr(user, 'activated', False):
            raise UserAlreadyActivatedError

        params = {
            'sendEmail': send_email
            }

        url = 'users/%s/lifecycle/activate' % user.id
        response = self._make_request(url, method='POST', params=params)
        check_for_error(response, 'ALREADY_ACTIVATED', UserAlreadyActivatedError)
        return response.json()
