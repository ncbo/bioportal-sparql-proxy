from django.conf.urls.defaults import patterns, include, url
import os
import settings as conf

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns (
        'views.sparqlproxy',
        (r'^/?$', 'main'),
        (r'^sparql/?$', 'sparql_auth'),
        (r'^examples/?$', 'examples'),
        (r'^apikeys/?$', 'apikeys'),
)
        

