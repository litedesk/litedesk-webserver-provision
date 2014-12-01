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


from django.conf import settings
from django.contrib import admin
from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

from authentication.views import SessionView
from tenants.views import AccountView, TenantView


urlpatterns = patterns(
    '',
    url(r'^api/session', SessionView.as_view(), name='session'),
)

urlpatterns += patterns(
    'tenants.views',
    url(r'^api/account/(?P<username>[\w.\+\-_]+)$', AccountView.as_view(), name='account'),
    url(r'^api/tenant$', TenantView.as_view(), name='tenant-detail'),
    url(r'^api/tenant/', include('tenants.urls')),
)

urlpatterns += patterns(
    'provisioning.views',
    url(r'^api/provisioning/', include('provisioning.urls')),
)

urlpatterns += patterns(
    'accounting.views',
    url(r'^api/accounting/', include('accounting.urls')),
)

urlpatterns += patterns(
    'catalog.views',
    url(r'^api/catalog/', include('catalog.urls')),
)

urlpatterns += patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
)


if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns(
        '',
        url(r'^/?$', RedirectView.as_view(url='/static/index.html')),
    )

    for static_url, doc_root in getattr(settings, 'EXTRA_STATIC_ROOTS', []):
        urlpatterns += static(static_url, document_root=doc_root)
