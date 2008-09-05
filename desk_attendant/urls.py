from django.conf.urls.defaults import *
from views import index, apply, application, admin_list, admin_individual, csv_export

urlpatterns = patterns('',
    (r'^$', index),
    (r'^apply/$', apply),
    (r'^application/(?P<id>\d+)/$', application),
    (r'^admin/$', admin_list),
    (r'^admin/(?P<id>\d+)/$', admin_individual),
    (r'^admin/export/$', csv_export),
)
