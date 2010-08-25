from django.http import HttpResponse


def job(request, job_name):
    return HttpResponse(job_name)
