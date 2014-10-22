#!/usr/bin/env python
#-*- coding: utf-8 -*-

import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics

import models
import permissions
import serializers


class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter()
    first_name = django_filters.CharFilter()
    last_name = django_filters.CharFilter()
    status = django_filters.CharFilter()

    class Meta:
        model = models.User
        fields = ['status', 'username', 'first_name', 'last_name']


class AccountView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'username'
    permission_classes = (permissions.IsAdminOrTenantPrimaryContact, )
    serializer_class = serializers.AccountSerializer
    model = get_user_model()


class TenantView(generics.RetrieveUpdateAPIView):
    permission_classes = (permissions.IsAdminOrTenantPrimaryContact, )
    serializer_class = serializers.TenantSerializer
    model = models.Tenant

    def get_object(self, *args, **kw):
        return self.request.user.tenant


class UserListView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    filter_class = UserFilter
    model = models.User
    paginate_by = 50

    def get_serializer_class(self, *args, **kw):
        return {
            'GET': serializers.UserSerializer
            }.get(self.request.method, serializers.NewUserSerializer)

    def filter_queryset(self, qs, *args, **kw):
        qs = super(UserListView, self).filter_queryset(qs)
        qs = qs.filter(tenant__primary_contact=self.request.user)
        term = self.request.GET.get('q')
        if term: qs = qs.filter(
                Q(first_name__istartswith=term) |
                Q(last_name__istartswith=term) |
                Q(username__startswith=term)
                )
        return qs


class UserView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAdminOrTenantPrimaryContact, )
    serializer_class = serializers.UserSerializer
    model = models.User


class UserGroupListView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsTenantPrimaryContact, )
    serializer_class = serializers.UserGroupSerializer
    model = models.UserGroup


class UserGroupView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAdminOrTenantPrimaryContact, )
    serializer_class = serializers.UserGroupSerializer
    model = models.UserGroup
