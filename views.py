import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

# importing * so it can capture the registry code
from wwu_housing.wwu_jobs.forms import *
from wwu_housing.data import Person

from models import Applicant, Application, ApplicationComponentPart, Component, Job
from utils import get_application_component_status


def job(request, job_slug):
    job = get_object_or_404(Job.objects.posted(), slug=job_slug)
    context = {"job": job}
    return render_to_response("jobs/job_detail.html", context, context_instance=RequestContext(request))

def has_conduct(person):
    cursor = connection.cursor()
    cursor.execute('SELECT id FROM conduct.students WHERE stunum = %s', [person.student_id])
    id = cursor.fetchone()
    if id:
        return id[0]
    else:
        return False


@login_required
def admin(request, job_slug):
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    apps = []
    addresses = ["Birnam", "Ridgeway", "Buchanan", "Edens", "Fairhave", "Higginson", "Highland", "Mathes", "Nash"]
    for applicant in job.application_set.all():
        person = Person.query.get(applicant.applicant.user.username)
        app = {}
        app['username'] = person.username
        app['first_name'] = person.first_name
        app['last_name'] = person.last_name
        app['gpa'] = person.gpa
        app['is_submitted'] = applicant.is_submitted
        addy = ""
        for address in person.addresses:
            if address.street_line_1.partition(' ')[0] in addresses:
                addy = address.street_line_1

        if addy:
            app["address"] = addy
        else:
            app["address"] = "Off campus"
        app["conduct_id"] = has_conduct(person)
        apps.append(app)

    apps.sort(key=lambda apps: apps['is_submitted'])
    statuses = ["In Progess", "Submitted", "Reviewing", "Interview Offered", "Interview Scheduled", "Denied", "Offered"]
    status = ["In Progess", "Submitted", "Reviewing", "Interview Offered", "Interview Scheduled", "Denied", "Offered"]
    colors = {"Submitted": "#FF9999", 
              "Reviewing": "#FFFF80", 
              "Interview Offered": "#99D699", 
              "Interview Scheduled": "#99FFFF", 
              "Denied": "white", 
              "Offered": "white"}
    context = {"apps": apps,
               "colors": colors, 
               "status": status, 
               "statuses": statuses}
    return render_to_response("jobs/admin.html", context, context_instance=RequestContext(request))

@login_required
def applicant(request, job_slug, applicant_slug):
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    applicant = Applicant.objects.get(user=request.user)
    application = Application.objects.get(applicant=applicant, job=job)
    context = {"applicant": applicant,
               "job": job,
               "application": application}
    return render_to_response("jobs/applicant.html", context, context_instance=RequestContext(request))

@login_required
def application(request, job_slug):
    try:
        job = Job.objects.posted().get(slug=job_slug)
    except Job.DoesNotExist:
        return HttpResponseRedirect(reverse("jobs_index"))

    application_exists = Application.objects.filter(
        job=job,
        applicant__user=request.user
    ).count() > 0

    # Redirect the user to the job's website if the job isn't open.
    if not job.is_open() and not application_exists:
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

    # Is the user submitting their application?
    if request.POST and request.POST.has_key(u"submit"):
        can_submit = True
        for component in job.component_set.all():
            if component.is_required:
                is_complete = get_application_component_status(application, component)[0]
                if not all(is_complete):
                    can_submit = False
        if can_submit:
            application.is_submitted = True
            application.end_datetime = datetime.datetime.now()
            application.save()
            message = u"<strong>Congratulations!</strong> Your application was successfully submitted."
            messages.success(request, message)
        else:
            message = u"<strong>Your application was not submitted.</strong> Please complete your application before submitting it."
            messages.error(request, message)

    context = {
        "application": application,
        "job": job
    }
    return render_to_response(
        "jobs/application.html",
        context,
        context_instance=RequestContext(request)
    )


@login_required
def component(request, job_slug, component_slug):
    try:
        job = Job.objects.posted().get(slug=job_slug)
    except Job.DoesNotExist:
        return HttpResponseRedirect(reverse("jobs_index"))

    applicant = Applicant.objects.get(user=request.user)
    application, created = Application.objects.get_or_create(job=job, applicant=applicant)
    component = get_object_or_404(job.component_set, slug=component_slug)
    component_parts = component.componentpart_set.all()

    all_forms_valid = True
    has_file_field = False
    for component_part in component_parts:
        # Try to find the an existing response for this component part for this
        # application. Otherwise, create an unsaved application component part.
        try:
            application_component_part = ApplicationComponentPart.objects.get(
                application=application,
                component_part=component_part
            )
            instance = application_component_part.content_object
        except ApplicationComponentPart.DoesNotExist:
            application_component_part = ApplicationComponentPart(
                application=application,
                component_part=component_part
            )
            instance = None

        content_type = component_part.content_type
        form_cls = registry.get(content_type.app_label).get(content_type.model)
        form = form_cls(request.POST or None, request.FILES or None,
                        instance=instance, prefix=component_part.id)

        if not has_file_field and form.is_multipart():
            has_file_field = True

        if form.is_valid() and not application.is_submitted:
            # Save the result of the form's process method as the application
            # component part's content which will serve as the initial instance
            # for this form.
            response = form.process(component_part)
            application_component_part.content_object = response
            application_component_part.save()
        else:
            all_forms_valid = False

        component_part.form = form

    # Only redirect if all forms validated.
    if all_forms_valid:
        return HttpResponseRedirect(job.get_application_url())

    return render_to_response(
        "jobs/component.html",
        {"application": application,
         "component": component,
         "component_parts": component_parts,
         "has_file_field": has_file_field},
        context_instance=RequestContext(request)
    )
