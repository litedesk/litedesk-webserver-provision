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
import re
import json

import requests

# FIXME: The check_for_error, check_is_known_error response should be
# refactored to use the check_exception_response decorator.
ERROR_RESPONSES = {
    'ALREADY_ACTIVATED': {
        'summary': 'Activation failed because the user is already active',
        'code': 'E0000016'
        },
    'ALREADY_REGISTERED': {
        'summary': 'login: An object with this field already exists '
        'in the current organization',
        'code': 'E0000001'
        }
    }


def check_exception_response(exception_class):
    def decorator(func):
        def proxy(self, *args, **kw):
            try:
                result = func(self, *args, **kw)
            except requests.HTTPError, http_error:
                error_response = http_error.response
                if exception_class.checking_function(error_response):
                    raise exception_class(exception_class.get_error_message(error_response))
                else:
                    raise http_error
            return result
        return proxy
    return decorator


def check_for_error(response, key, exception):
    try:
        response.raise_for_status()
    except requests.HTTPError, exc:
        if check_is_known_error_response(response, key):
            raise exception
        else:
            raise exc


def check_is_known_error_response(response, key):
    try:
        known_error_response = ERROR_RESPONSES[key]
        error_response = response.json()
        error_summaries = [e.get('errorSummary') for e in error_response.get('errorCauses')]
        if error_response.get('errorResponse'):
            error_summaries.append(error_response['errorResponse'])
        return all([
            known_error_response['code'] == error_response.get('errorCode'),
            known_error_response['summary'] in error_summaries
            ])
    except KeyError:
        return False


class OktaException(Exception):
    PATTERN = None
    ERROR_CODE = None
    ERROR_MESSAGE_TEMPLATE = None

    @classmethod
    def get_error_message(cls, error_response):
        response_data = error_response.json()
        summary = response_data.get('errorSummary')
        match = re.match(cls.PATTERN, summary)
        groups = match and match.groups()
        return cls.ERROR_MESSAGE_TEMPLATE % (groups[0])

    @classmethod
    def checking_function(cls, response):
        response_data = response.json()
        return all([
            response_data.get('errorCode') == cls.ERROR_CODE,
            re.match(cls.PATTERN, response_data.get('errorSummary', '')) is not None
            ])


class ResourceDoesNotExistError(OktaException):
    pass


class UserAlreadyExistsError(OktaException):
    pass


class UserAlreadyActivatedError(OktaException):
    pass


class UserNotActiveError(OktaException):
    PATTERN = r'Not found: Resource not found: (.*) \(User\)'
    ERROR_CODE = 'E0000007'
    ERROR_MESSAGE_TEMPLATE = 'User %s not found, or not active'


class UserApplicationNotFound(OktaException):
    PATTERN = r'Not found: Resource not found: (.*) \(AppUser\)'
    ERROR_CODE = 'E0000007'
    ERROR_MESSAGE_TEMPLATE = 'User Application %s not assigned'


class Resource(object):
    def __init__(self, client, *args, **kw):
        self._client = client
        for k, v in kw.items():
            setattr(self, k, v)


class User(Resource):
    ENDPOINT_ROOT = 'users'

    @check_exception_response(UserNotActiveError)
    def deactivate(self):
        url = 'users/%s/lifecycle/deactivate' % self.id
        response = self._client._make_request(url, method='POST')
        response.raise_for_status()


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

    @check_exception_response(UserApplicationNotFound)
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
        response = self._make_request('users', method='GET')
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
        check_for_error(response, 'ALREADY_REGISTERED', UserAlreadyExistsError)
        return response.json()

    def activate_user(self, user, send_email=True):
        status = getattr(user, 'status', None)
        if status is not None and status not in ('DEPROVISIONED', 'STAGED'):
            raise UserAlreadyActivatedError

        params = {
            'sendEmail': send_email
            }

        url = 'users/%s/lifecycle/activate' % user.id
        response = self._make_request(url, method='POST', params=params)
        check_for_error(response, 'ALREADY_ACTIVATED', UserAlreadyActivatedError)
        return response.json()

    def expire_password(self, user, tmp_passwd=False):
        url = 'users/{0}/lifecycle/expire_password?tempPassword={1}'.format(
            user.id,
            str(tmp_passwd).lower()
            )
        response = self._make_request(url, method='POST')
        response.raise_for_status()
        return response.json()

    def last_sso_event(self, user, app):
        filter_strings = [
            'action.objectType eq "app.auth.sso"',
            'target.id eq "%s"' % user,
            'target.id eq "%s"' % app
            ]
        params = {'filter': ' and '.join(filter_strings)}
        response = self._make_request('events', method='GET', params=params)
        response.raise_for_status()
        json = response.json()
        if len(json) == 0:
            return None
        else:
            return json[-1]

    def user_applications(self, user):
        params = {'filter': 'user.id eq "%s"' % (user.id)}
        response = self._make_request('apps', method='GET', params=params)
        response.raise_for_status()
        #print response.headers
        return response.json()
