"""Provide XBlock urls"""

from django.conf.urls import include, patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin

from workbench.scenarios import init_scenarios

admin.autodiscover()

init_scenarios()

urlpatterns = patterns(
    'workbench.views',
    url(r'^$', 'index', name='workbench_index'),
    url(
        r'^scenario/(?P<scenario_id>[^/]+)/(?P<view_name>[^/]+)/$',
        'show_scenario',
        name='scenario'
    ),
    url(
        r'^scenario/(?P<scenario_id>[^/]+)/$',
        'show_scenario',
        name='workbench_show_scenario'
    ),
    url(
        r'^view/(?P<scenario_id>[^/]+)/(?P<view_name>[^/]+)/$',
        'show_scenario',
        {'template': 'workbench/blockview.html'}
    ),
    url(
        r'^view/(?P<scenario_id>[^/]+)/$',
        'show_scenario',
        {'template': 'workbench/blockview.html'}
    ),
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
    url(
        r'^reset_state$',
        'reset_state',
        name='reset_state'
    ),

    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
