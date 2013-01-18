from django.conf.urls import patterns, url

urlpatterns = patterns('remote.views',
    url(r'^view_direct/(?P<usage_id>\w+)/(?P<view_name>\w+)', 'view'),
    url(r'^handler_direct/(?P<usage_id>\w+)/(?P<handler_name>\w+)', 'handler_direct'),
    url(r'^handler_tunneled/(?P<usage_id>\w+)/(?P<handler_name>\w+)', 'handler_tunneled'),
)
