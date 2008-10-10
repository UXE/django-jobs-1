from django.conf.urls.defaults import *

from wwu_housing.views import files


urlpatterns = patterns('',
    (r'^desk-attendant/', include('wwu_housing.jobs.desk_attendant.urls')),
    url(r'^files/(?P<path>[\-_/\.\w]+)/$', files, {"base_path": "jobs"}, name="jobs_files"),
)
