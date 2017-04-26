#  Copyright (c) 2016-2017 Oleksandr Tymoshenko <gonzo@bluezbox.com>
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
#  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#  SUCH DAMAGE.
from django.conf.urls import include, url
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^version/?$', views.get_version, name='version'),
    url(r'^(?P<branch_id>[0-9]+)/$', views.branch, name='branch'),
    url(r'^(?P<branch_id>[0-9]+)/setfilter$', views.setfilter, name='setfilter'),
    url(r'^(?P<branch_id>[0-9]+)/newtoken$', views.generate_new_token, name='newtoken'),
    url(r'^(?P<branch_id>[0-9]+)/mfc$', views.mfcbasket, name='mfcbasket'),
    url(r'^(?P<branch_id>[0-9]+)/mfc/helper$', views.mfchelper, name='mfchelper'),
    url(r'^(?P<branch_id>[0-9]+)/mfc/(?P<username>[a-z0-9]+)/(?P<token>.+)$', views.mfcshare, name='mfcshare'),
    url(r'^mfcbasket/json$', views.basket, name='mfcbasket'),
    url(r'^mfcbasket/add$', views.addrevision, name='addrevision'),
    url(r'^mfcbasket/remove$', views.delrevision, name='delrevision'),
    url(r'^mfcbasket/clear$', views.clearbasket, name='clearbasket'),
    url(r'^commit/(?P<revision>[0-9]+)/comment$', views.comment_commit, name='comment_commit'),
    url(r'^commit/(?P<revision>[0-9]+)/fixdeps$', views.fix_commit_dependencies, name='fixdeps_commit'),
    url('^', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
