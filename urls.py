from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^desk-attendant/', include('wwu_housing.jobs.desk_attendant.urls')),
)
