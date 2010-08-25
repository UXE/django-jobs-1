from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list

from models import Job
from views import job


urlpatterns = patterns("",
    url(r"^$", object_list, {"queryset": Job.objects.posted(), "template_object_name": "job"}, name="jobs_index"),
    url(r"^(?P<job_name>[-\w]+)/$", job, name="jobs_job")
)
