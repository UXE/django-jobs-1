from django.conf.urls.defaults import *
from wwu_housing.jobs.models import Job
from views import index, apply, application, admin_list, admin_individual, csv_export

# TODO: move this queryset into the index and store the job object in the user's session.
#view_dict = {'job': Job.objects.filter(title='Desk Attendant').latest('open_datetime'),}

urlpatterns = patterns('',
#     (r'^$', index, view_dict),
#     (r'^apply/$', apply, view_dict),
#     #(r'^application/(?P<id>\d+)/$', application),
#     (r'^admin/$', admin_list, view_dict),
#     (r'^admin/(?P<id>\d+)/$', admin_individual, view_dict)
#     #(r'^admin/export/$', csv_export, view_dict),
)
