from django.conf.urls import patterns, url

urlpatterns = patterns('remote.views',
    url(r'^view/(?P<usage_id>\w+)/(?P<view_name>\w+)', 'view'),
    url(r'^handler/(?P<usage_id>\w+)/(?P<handler_name>\w+)', 'handler'),
)
