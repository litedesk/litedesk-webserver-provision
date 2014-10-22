#!/usr/bin/env python
#-*- coding: utf-8 -*-

from django.conf.urls import url, patterns

import views

urlpatterns = patterns(
    '',
    url(r'^session$', views.SessionView.as_view(), name='session'),
    url(r'^login$', views.LoginView.as_view(), name='login'),
    url(r'^signup$', views.SignupView.as_view(), name='signup'),
    )
