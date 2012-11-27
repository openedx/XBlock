from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('xmoduledebugger.views',
    url(r'^$', 'index', name='index'),
    url(r'^settings$', 'settings', name='settings'),
    url(r'^(?P<module_name>[^/]+)$', 'module', name='module'),

    url(r'^(?P<module_name>[^/]+)/(?P<handler>[^/]*)', 'handler', name='handler'),
    # Examples:
    # url(r'^$', 'xmoduledebugger.views.home', name='home'),
    # url(r'^xmoduledebugger/', include('xmoduledebugger.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
