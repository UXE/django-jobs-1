from django.conf.urls.defaults import *
from wwu_housing.jobs.models import Job
from views import index, apply, admin

view_dict = {'job': Job.objects.filter(title='Desk Attendant').latest('open_datetime')}

urlpatterns = patterns('',
    (r'^$', index, view_dict),
    (r'^apply/$', apply, view_dict),
    #(r'^admin/$', admin, view_dict),
    (r'^admin/(?P<id>\d+)/$', admin, view_dict)
)
