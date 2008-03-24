from django.conf.urls.defaults import *
from views import index

urlpatterns = patterns('',
    (r'^$', index),
)
