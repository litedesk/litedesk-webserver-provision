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

from rest_framework import serializers

import models


class OfferSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='offer-detail')

    class Meta:
        model = models.Offer
        fields = ('url', 'name', 'currency', 'price', 'setup_price', 'status')
        read_only_fields = ('name', 'asset', 'currency', )
