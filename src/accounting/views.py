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

import calendar
import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants import permissions

import models


class CostView(APIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )

    def _get_interval(self):
        today = datetime.date.today()
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')

        if start is not None:
            start_year, start_month = (int(d) for d in start.split('-'))
            start_date = datetime.date(year=start_year, month=start_month, day=1)
        else:
            start_date = today - relativedelta(months=11)

        if end is not None:
            end_year, end_month = (int(d) for d in end.split('-'))
        else:
            end_year, end_month = today.year, today.month

        end_day = calendar.monthrange(end_year, end_month)[-1]
        end_date = datetime.date(year=end_year, month=end_month, day=end_day)

        if start_date > end_date:
            raise ValueError('%s -> %s is an invalid interval' % (start_date, end_date))

        return (start_date, end_date)

    def _make_periods(self, start, end):
        while start.year <= end.year and not start.month > end.month:
            dt = datetime.date(year=start.year, month=start.month, day=1)
            start += relativedelta(months=1)
            end_day = calendar.monthrange(dt.year, dt.month)[-1]
            yield dt, datetime.date(year=dt.year, month=dt.month, day=end_day)
        raise StopIteration

    def _serialize(self, category, qs, start_date, end_date):
        expenses = self._expenses_with_category(qs, category)
        return [{
            'date': '%4d-%02d' % (start.year, start.month),
            'cost': round(self._break_down_by_period(expenses, start, end), 2)
            } for start, end in self._make_periods(start_date, end_date)]

    def _expenses_with_category(self, qs, category):
        raise NotImplementedError

    def _break_down_by_period(self, qs, start, end):
        raise NotImplementedError

    def get_queryset(self, *args, **kw):
        raise NotImplementedError

    def get(self, request, *args, **kw):
        qs = self.get_queryset()
        start_date, end_date = self._get_interval()

        return Response(
            {c: self._serialize(c, qs, start_date, end_date) for c in models.EXPENSE_CATEGORIES}
            )


class ContractCostView(CostView):

    def get_queryset(self, *args, **kw):
        return models.Contract.objects.filter(tenant=self.request.user.tenant)

    def _expenses_with_category(self, qs, category):
        return qs.filter(category=category)

    def _break_down_by_period(self, qs, start, end):
        active = qs.exclude(start_date__gt=end).exclude(end_date__lt=start)
        return sum([it.offer.__subclassed__.monthly_cost for it in active])


class UserCostView(CostView):

    @property
    def total_users(self):
        if hasattr(self, '_total_users'): return self._total_users

        self._total_users = self.request.user.tenant.user_set.count()
        return self._total_users

    def get_queryset(self, *args, **kw):
        return models.Charge.objects.filter(user__tenant=self.request.user.tenant)

    def _expenses_with_category(self, qs, category):
        return qs.filter(contract__category=category)

    def _break_down_by_period(self, qs, start, end):
        active = qs.exclude(start_date__gt=end).exclude(end_date__lt=start)
        return sum([Decimal(str(it.amount)) / self.total_users for it in active])
