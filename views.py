from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from models import Job


def job(request, job_slug):
    job = get_object_or_404(Job.objects.posted(), slug=job_slug)
    return HttpResponse(job.title)
