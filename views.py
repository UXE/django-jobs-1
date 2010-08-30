from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from models import Applicant, Application, Job


def job(request, job_slug):
    job = get_object_or_404(Job.objects.posted(), slug=job_slug)
    context = {"job": job}
    return render_to_response("jobs/job_detail.html", context, context_instance=RequestContext(request))


@login_required
def application(request, job_slug):
    job = get_object_or_404(Job.objects.posted(), slug=job_slug)

    # Redirect the user to the job's website if the job isn't open.
    if not job.is_open():
        if job.will_open():
            message = "Applications for %s are not open yet. They will open %s." % (job, job.open_datetime)
        else:
            message = "Applications for %s are closed." % job

        messages.warning(request, message)
        return HttpResponseRedirect(job.get_absolute_url())

    applicant, created = Applicant.objects.get_or_create(user=request.user)
    application, created = Application.objects.get_or_create(
        applicant=applicant,
        job=job
    )

    return HttpResponse(job.title)
