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


from django.contrib import auth
from django.contrib.auth import login
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework import status

import permissions
import serializers


class SessionView(APIView):
    def get_serializer(self, *args, **kw):
        serializer_class = {
            'POST': serializers.LoginSerializer
            }.get(self.request.method, serializers.SessionSerializer)

        kw['context'] = {
            'request': self.request
            }

        return serializer_class(*args, **kw)

    def get_object(self):
        return self.request.session

    def get(self, request, *args, **kw):
        if not request.user.is_authenticated():
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def post(self, request, *args, **kw):
        serializer = self.get_serializer(data=request.DATA)
        if serializer.is_valid():
            login(request, serializer.object)
            location_header = {'Location': reverse('session', request=request)}
            return Response(status=status.HTTP_201_CREATED, headers=location_header)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kw):
        auth.logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SignupView(generics.CreateAPIView):
    serializer_class = serializers.SignupSerializer
    permission_classes = (permissions.UnauthenticatedUser,)

    def post_save(self, user, **kw):
        login(self.request, user)
