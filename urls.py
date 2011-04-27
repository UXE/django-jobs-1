from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list

from wwu_housing.wwu_jobs.views import interview, positionplacement , interview_creation
from wwu_housing.desk_attendant.views  import admin_individual, admin_list, apply
from models import Job
from views import admin, applicant, application, component, create_admin_csv, export_application, job, jobs_index


urlpatterns = patterns("",
#url(r"^$", object_list, {"queryset": Job.objects.posted(), "template_object_name": "job"}, name="jobs_index"),
    url(r"^$", jobs_index, name="jobs_index"),
    url(r"^(?P<job_slug>[-\w]+)/$", job, name="jobs_job"),
    url(r"^(?P<job_slug>[-\w]+)/interview/$", interview, name="jobs_interview"),
    url(r"^(?P<job_slug>[-\w]+)/interview_creation/$", interview_creation, name="jobs_interview_creation"),
    url(r"^(?P<job_slug>[-\w]+)/admin/positionplacement/$", positionplacement, name="jobs_positionplacement"),
    url(r"^desk-attendant/admin/$", admin_list, name="da_admin_list"),
    url(r'^desk-attendant/admin/(?P<id>\d+)/$', admin_individual, name="da_admin"),
    url(r"^(?P<job_slug>[-\w]+)/admin/$", admin, name="jobs_job_admin"),
    url(r"^(?P<job_slug>[-\w]+)/admin/csv/$", create_admin_csv, name="jobs_job_admin_csv"),
    url(r"^(?P<job_slug>[-\w]+)/admin/export_application/$", export_application, name="jobs_job__export_application"),
    url(r"^(?P<job_slug>[-\w]+)/admin/(?P<applicant_slug>[-\w]+)/$", applicant, name="jobs_job_admin_applicant"),
    url(r"^desk-attendant/application/$", apply, name="da_apply"),
    url(r"^(?P<job_slug>[-\w]+)/application/$", application, name="jobs_application"),
    url(r"^(?P<job_slug>[-\w]+)/application/(?P<component_slug>[-\w]+)/$", component, name="jobs_component")
)
