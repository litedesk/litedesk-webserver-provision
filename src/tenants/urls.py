#!/usr/bin/env python
#-*- coding: utf-8 -*-

from django.conf.urls import url, patterns

import views


urlpatterns = patterns(
    '',
    url(r'^users$', views.UserListView.as_view(), name='user-list'),
    url(r'^users/user/(?P<pk>\d+)$', views.UserView.as_view(), name='user-detail'),
    url(r'^groups$', views.UserGroupListView.as_view(), name='user-group-list'),
    url(r'^group/(?P<pk>\d+)$', views.UserGroupView.as_view(), name='user-group-detail'),
)
