from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<branch_id>[0-9]+)/$', views.branch, name='branch'),
    url(r'^(?P<branch_id>[0-9]+)/setfilter$', views.setfilter, name='setfilter'),
    url(r'^(?P<branch_id>[0-9]+)/mfc$', views.mfchelper, name='mfchelper'),
    url(r'^mfcbasket/json$', views.basket, name='mfcbasket'),
    url(r'^mfcbasket/add$', views.addrevision, name='addrevision'),
    url(r'^mfcbasket/remove$', views.delrevision, name='delrevision'),
    url(r'^mfcbasket/clear$', views.clearbasket, name='clearbasket'),
    url(r'^commit/(?P<revision>[0-9]+)$', views.commit, name='commit'),
]
