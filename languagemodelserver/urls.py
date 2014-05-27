from django.conf.urls import patterns, include, url
from rest_framework import routers
from languagemodel import views

from django.contrib import admin
admin.autodiscover()


router = routers.DefaultRouter()
router.register(r'ngrams', views.NgramViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'languagemodelserver.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^', include(router.urls)),
)
