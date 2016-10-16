from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<branch_id>[0-9]+)/$', views.branch, name='branch'),
    url(r'^(?P<branch_id>[0-9]+)/setfilter$', views.setfilter, name='setfilter'),
    url(r'^(?P<branch_id>[0-9]+)/mfc$', views.mfchelper, name='mfchelper'),
]
