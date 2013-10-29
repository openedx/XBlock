"""Provide XBlock urls"""

from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# This import is here simply to get this file imported explicitly.
# If it fails to import later, it's inside the url resolver, and we
# don't see the actual errors.
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
        'handler',
        name='handler'
    ),
    url(r'^resource/(?P<package>[^/]+)/(?P<resource>.*)$', 'package_resource', name='package_resource'),
)

urlpatterns += staticfiles_urlpatterns()
