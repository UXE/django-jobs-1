import csv, datetime, os

from string import Template

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.db import connection, transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.mail import EmailMessage, mail_admins
from django.core.urlresolvers import reverse
from django.conf import settings

# importing * so it can capture the registry code
from wwu_housing.wwu_jobs.forms import *

from wwu_housing.data import Person

from forms import AdminApplicationForm
from models import AdminApplication, Applicant, Application, ApplicationComponentPart, ApplicationEmail, ApplicationStatus, Component, Job, JobUser, User

from utils import get_application_component_status


def job(request, job_slug):
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    if job.close_datetime > datetime.datetime.now():
        job_open = True
    else:
        job_open = False
    context = {"job": job,
               "job_open": job_open}
    return render_to_response("jobs/job_detail.html", context, context_instance=RequestContext(request))

def jobs_index(request):
    context = {}
    jobs = Job.objects.all()
    job_list = []
    applications = []

    if request.user.is_authenticated():
        user = request.user
        applicant = Applicant.objects.filter(user=user)
        applications = Application.objects.filter(applicant=applicant)

    for eachjob in jobs:
        job = {}
        #Check if they are an admin or not
        try:
            administrator = JobUser.objects.get(user=request.user, job=eachjob)
        except (JobUser.DoesNotExist, TypeError):
            administrator = None


        #check if user has a job app for each job
        for application in applications:
            if application.job == eachjob:
                job["job"] = eachjob
                job["applied"] = True
                job["admin"] = administrator
                #if the application is submitted obtain status
                if application.is_submitted:
                    try:
                        application_status = AdminApplication.objects.get(
                                                        application=application)
                        job["app_status"] = application_status.status.status
                        if application_status.status.status in [u"Interview Scheduled", u"Interview Offered"]:
                            job["interview_status"] = application_status.status.status
                            try:
                                interview = Interview.objects.get(job=application.job,
                                                            application=application)
                                job["interview_date"] = interview.datetime
                            except Interview.DoesNotExist:
                                job["interview_date"] = None
                        job_list.append(job)
                    except AdminApplication.DoesNotExist:
                        job["app_status"] = "You have successfully submitted your application"
                        job_list.append(job)
                #else if job has app that has not been submitted and is still open add it to list
                else:
                    if eachjob.close_datetime > datetime.datetime.now():
                        job["app_status"] = "In Progress"
                        job_list.append(job)
        #include job's that are still open
        if not job:
            if eachjob.close_datetime > datetime.datetime.now():
                job["job"] = eachjob
                job["applied"] = None
                job["admin"] = administrator
                job_list.append(job)

    context = {"job_list" : job_list,
               "user" : request.user}
    return render_to_response("jobs/index.html", context, context_instance=RequestContext(request))

def has_conduct(person):
    cursor = connection.cursor()
    cursor.execute("SELECT stunum FROM conduct.students WHERE stunum = %s", [person.student_id])
    id = cursor.fetchone()
    if id:
        return id[0]
    else:
        return False

@login_required
def create_admin_csv(request, job_slug):
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    try:
        administrator = JobUser.objects.get(user=request.user, job=job)
    except JobUser.DoesNotExist:
        if not request.user.is_superuser:
            raise Http404

    response = HttpResponse(mimetype="text/csv")
    response["Content-Disposition"] = 'attachment; filename=%s.csv' % job_slug

    writer = csv.writer(response)
    writer.writerow(["First Name", "Last Name", "GPA"])
    for application in job.application_set.all():
        person = Person.query.get(application.applicant.user.username)

        writer.writerow([person.first_name, person.last_name, person.gpa])

    return response

@login_required
def admin(request, job_slug):
    post_data = request.POST or None
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    try:
        administrator = JobUser.objects.get(user=request.user, job=job)
    except JobUser.DoesNotExist:
        if not request.user.is_superuser:
            raise Http404
        else:
            administrator = True

    apps = []
    forms = []
    addresses = ["Birnam", "Ridgeway", "Buchanan", "Edens", "Fairhaven", "Higginson", "Highland", "Mathes", "Nash"]

    for application in job.application_set.all():
        if not application.applicationcomponentpart_set.all():
            continue
        person = Person.query.get(application.applicant.user.username)
        user = User.objects.get(username=person.username)
        applicant_full = Applicant.objects.get(user=user)
        app = {}
        app['username'] = person.username
        app['first_name'] = person.first_name
        app['last_name'] = person.last_name
        app['gpa'] = person.gpa
        app['is_submitted'] = application.is_submitted
        addy = ""
        for address in person.addresses:
            if address.street_line_1.partition(' ')[0] in addresses:
                addy = address.street_line_1
        if addy:
            app["address"] = addy
        else:
            app["address"] = "Off campus"

        app["conduct_id"] = has_conduct(person)
        try:
            instance = AdminApplication.objects.get(application=application)
        except AdminApplication.DoesNotExist:
            if app['is_submitted']:
                status = ApplicationStatus.objects.get(status="Submitted")
            else:
                status = ApplicationStatus.objects.get(status="In Progress")
            instance = AdminApplication(status=status, application=application)
        prefix = "%s" % (application.id)
        form = AdminApplicationForm(post_data,
                                     prefix=prefix,
                                     instance=instance)
        app["form"] = form
        app["application"] = application
        if administrator and form.is_valid():
            form.save()
            if form.initial["status"] != form.cleaned_data["status"].id:
                try:
                    application_email = ApplicationEmail.objects.get(status=form.cleaned_data["status"], job=job)
                except ApplicationEmail.DoesNotExist:
                    application_email = None
                if not settings.DEBUG:
                    if application_email and person.email:
                        subject = application_email.subject
                        from_email = application_email.sender
                        to_email = (person.email,)
                        message_content = Template(application_email.content)
                        message = message_content.substitute(name=person.first_name)
                        email = EmailMessage(subject, message, from_email, to_email)
                        email.send()
                        comment = "%s email has been sent" % (form.cleaned_data["status"])
                        user = request.user or None
                        content_type = ContentType.objects.get(name="application")
                        Comment.objects.create(content_type=content_type,
                                               object_pk=application.id,
                                               site=Site.objects.get_current(),
                                               user=user,
                                               comment=comment)
                    elif application_email:
                        subject = "%s %s for position %s has no email" & (person.first_name, person.last_name, job)
                        message = "%s %s (%s) does not have an email address. They applied for %s and were supposed to receive %s email." % (person.first_name, person.last_name, person.student_id, job, application_email.subject)
                        mail_admins(subject, message)

        apps.append(app)
        forms.append(form)
    if forms and all(form.is_valid() for form in forms):
        messages.success(request, "Changes saved successfully")
        return HttpResponseRedirect(reverse("jobs_job_admin",
                                            args=[job_slug]))
    apps.sort(key=lambda apps: apps["form"].instance.status.id)
    colors = {"Submitted": "#FF9999",
              "Reviewing": "#FFFF80",
              "Interview Offered": "#99D699",
              "Interview Scheduled": "#99FFFF",
              "Denied": "white",
              "Offered": "white"}
    context = {"apps": apps,
               "colors": colors,
               "admin": administrator}

    return render_to_response("jobs/admin.html", context, context_instance=RequestContext(request))

@login_required
def applicant(request, job_slug, applicant_slug):
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    try:
        administrator = JobUser.objects.get(user=request.user, job=job)
    except JobUser.DoesNotExist:
        if not request.user.is_superuser:
            raise Http404

    user = User.objects.get(username=applicant_slug)
    applicant = Applicant.objects.get(user=user)
    application = Application.objects.get(applicant=applicant, job=job)
    components = []
    for component_part in application.component_parts.all():
        responses = {}
        response = application.applicationcomponentpart_set.get(application=application, component_part=component_part)
        if not response.content_type:
            responses["type"] = "none"
        elif response.content_type.name == "file response":
            responses["response"] = response.content_object.file.name
            responses["type"] = "file"
        elif response.content_type.name == "work history response":
            responses["response"] = response.content_object
            responses["type"] = "work_history"
        elif response.content_type.name == "placement preference response":
            responses["response"] = response.content_object
            responses["type"] = "placement_preference"
        else:
            responses["response"] = response.content_object.response
            responses["type"] = "normal"
        responses["component_part"] = component_part
        responses["component"] = response.component_part.component.name
        components.append(responses)

    components.sort(key= lambda responses: responses["component"])
    applicant_name = "%s %s" % (user.first_name, user.last_name)
    context = {"applicant_name": applicant_name,
               "components": components,
               "job_title": job.title}
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
