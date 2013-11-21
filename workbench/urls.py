"""Provide XBlock urls"""

from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from workbench.scenarios import init_scenarios


init_scenarios()

urlpatterns = patterns(
    'workbench.views',
    url(r'^$', 'index', name='index'),
    url(r'^scenario/(?P<scenario_id>[^/]+)/(?P<view_name>[^/]+)/$', 'show_scenario', name='scenario'),
    url(r'^scenario/(?P<scenario_id>[^/]+)/$', 'show_scenario'),

    url(r'^view/(?P<scenario_id>[^/]+)/(?P<view_name>[^/]+)/$', 'show_scenario', {'template': 'blockview.html'}),
    url(r'^view/(?P<scenario_id>[^/]+)/$', 'show_scenario', {'template': 'blockview.html'}),

    url(
        r'^handler/(?P<usage_id>[^/]+)/(?P<handler_slug>[^/]*)(?:/(?P<suffix>.*))?$',
        'handler', {'authenticated': True},
        name='handler'
    ),
    url(
        r'^unauth_handler/(?P<usage_id>[^/]+)/(?P<handler_slug>[^/]*)(?:/(?P<suffix>.*))?$',
        'handler', {'authenticated': False},
        name='unauth_handler'
    ),
    url(
        r'^resource/(?P<block_type>[^/]+)/(?P<resource>.*)$',
        'package_resource',
        name='package_resource'
    ),
)

urlpatterns += staticfiles_urlpatterns()
