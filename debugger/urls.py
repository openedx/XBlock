from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('debugger.views',
    url(r'^$', 'index', name='index'),
    url(r'^settings$', 'settings', name='settings'),
    url(r'^scenario/(?P<scenario_id>[^/]+)$', 'show_scenario', name='scenario'),
    url(r'^resource/(?P<package>[^/]+)/(?P<resource>.*)/?', 'package_resource', name='package_resource'),

    url(r'^(?P<usage_id>[^/]+)/(?P<handler>[^/]*)', 'handler', name='handler'),

    # Examples:
    # url(r'^$', 'debugger.views.home', name='home'),
    # url(r'^debugger/', include('debugger.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
