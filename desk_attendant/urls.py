from django.conf.urls.defaults import *
from views import (index, apply, application, admin_list, admin_individual,
                    comment, csv_export)

urlpatterns = patterns('',
    (r'^$', index),
    (r'^apply/$', apply),
    (r'^application/(?P<id>\d+)/$', application),
    (r'^admin/$', admin_list),
    url(r'^admin/(?P<id>\d+)/$', admin_individual, name="desk_attendant_admin"),
    (r'^admin/export/$', csv_export),
    url(r"^comment/(\d+)/$", comment, name="desk_attendant_comment"),
)
