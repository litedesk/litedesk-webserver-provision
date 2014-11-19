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


from rest_framework import generics

from tenants import permissions
import models
import serializers


class OfferListView(generics.ListAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.OfferSerializer

    def get_queryset(self, *args, **kw):
        return self.request.user.tenant.offet_set.all()


class OfferView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.OfferSerializer
    model = models.Offer
