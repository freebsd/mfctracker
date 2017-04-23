from django.conf.urls import include, url
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<branch_id>[0-9]+)/$', views.branch, name='branch'),
    url(r'^(?P<branch_id>[0-9]+)/setfilter$', views.setfilter, name='setfilter'),
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
