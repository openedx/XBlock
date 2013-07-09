from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# This import is here simply to get this file imported explicitly.
# If it fails to import later, it's inside the url resolver, and we
# don't see the actual errors.
from workbench.scenarios import SCENARIOS   # pylint: disable=W0611

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    'workbench.views',
    url(r'^$', 'index', name='index'),
    url(r'^scenario/(?P<scenario_id>[^/]+)/(?P<view_name>[^/]+)/$', 'show_scenario', name='scenario'),
    url(r'^scenario/(?P<scenario_id>[^/]+)/$', 'show_scenario'),

    url(r'^view/(?P<scenario_id>[^/]+)/(?P<view_name>[^/]+)/$', 'show_scenario', {'template': 'blockview.html'}),
    url(r'^view/(?P<scenario_id>[^/]+)/$', 'show_scenario', {'template': 'blockview.html'}),

    url(r'^handler/(?P<usage_id>[^/]+)/(?P<handler_slug>[^/]*)/$', 'handler', name='handler'),
    url(r'^resource/(?P<package>[^/]+)/(?P<resource>.*)$', 'package_resource', name='package_resource'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
