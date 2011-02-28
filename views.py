import csv
import datetime
import os

from string import Template
from sqlalchemy import or_

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

from chunks.models import Chunk

# importing * so it can capture the registry code
from wwu_housing.wwu_jobs.forms import *
from wwu_housing.wwu_jobs.models import Interview
from wwu_housing.data import Person

from forms import AdminApplicationForm
from models import AdminApplication, Applicant, Application, ApplicationComponentPart, ApplicationEmail, ApplicationStatus, Component, Job, JobUser, User

from utils import get_application_component_status, _get_persons_for_job


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
        if eachjob.close_datetime > datetime.datetime.now():
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
                    #TODO: change so submitted app's don't show up if unaccessable
                    # using the closedate
                        try:
                            application_status = AdminApplication.objects.get(
                                                            application=application)
                            job["app_status"] = application_status.status
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
                        #change to use the .priotitydate instead
                        if eachjob.close_datetime > datetime.datetime.now():
                            job["app_status"] = "In Progress"
                            job_list.append(job)
            #include job's that are still open
            if not job:
                # change to use the .priotirydate instead
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
            return HttpResponse(status=401, content="401 Unauthorized Access", mimetype="text/plain")

    response = HttpResponse(mimetype="text/csv")
    response["Content-Disposition"] = 'attachment; filename=%s.csv' % job_slug

    writer = csv.writer(response)
    writer.writerow(["Student ID", "First Name", "Last Name", "Gender",
                     "Email", "Address", "GPA", "Ethnicity", "Status",
                     "Interview Location", "Interview Date"])

    persons = _get_persons_for_job(job)

    for application in job.application_set.all():
        if not application.applicationcomponentpart_set.all():
            continue
        person = persons[application.applicant.user.username]
        address = person.get_address_by_type("MA")
        if address:
            mailing_address = address.street_line_1
            if address.street_line_2:
                mailing_address = mailing_address + " " + address.street_line_2
            if address.street_line_3:
                mailing_address = mailing_address + " " + address.street_line_3
            mailing_address = "%s %s, %s %s" % (mailing_address, address.city,
                                                address.state, address.zip_code)
        else:
            mailing_address = ""

        try:
            interview = Interview.objects.get(job=application.job,
                                              application=application)
            interview_location = interview.location
            interview_date = interview.datetime.strftime("%A, %B %e at %I:%M %p")
        except Interview.DoesNotExist:
            interview_location = "None"
            interview_date = "None"

        writer.writerow([person.student_id, person.first_name,
                         person.last_name, person.gender, person.email,
                         mailing_address, person.gpa, person.ethnicity,
                         application.status, interview_location,
                         interview_date])

    return response


@login_required
def admin(request, job_slug):

    post_data = request.POST or None
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    try:
        administrator = JobUser.objects.get(user=request.user, job=job)
    except JobUser.DoesNotExist:
        if not request.user.is_superuser:
            return HttpResponse(content="401 Unauthorized: Access is denied due to invalid credentials.",
                                mimetype="text/plain", status=401)
        else:
            administrator = True

    persons = _get_persons_for_job(job)

    apps = []
    forms = []
    addresses = ["Birnam", "Ridgeway", "Buchanan", "Edens", "Fairhaven", "Higginson", "Highland", "Mathes", "Nash"]

    for application in job.application_set.all():
        if not application.applicationcomponentpart_set.all():
            continue
        person = persons[application.applicant.user.username]
        user = application.applicant.user
        applicant_full = Applicant.objects.get(user=user)
        app = {}
        app['username'] = person.username or person.student_id
        app['first_name'] = person.first_name
        app['last_name'] = person.last_name
        app['gpa'] = person.gpa
        app['is_submitted'] = application.is_submitted
        try:
            interview = Interview.objects.get(job=application.job,
                                              application=application)
            app['interview_date'] = interview.datetime.strftime("%B, %e at %I:%M %p")
        except Interview.DoesNotExist:
            app['interview_date'] = "None"
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
            if application.is_submitted or application.end_datetime:
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
                if form.cleaned_data["status"].status not in [u'Position Offered', u'Position Accepted']:
                    try:
                        application_email = ApplicationEmail.objects.get(status=form.cleaned_data["status"], job=job)
                    except ApplicationEmail.DoesNotExist:
                        application_email = None
                    if not settings.DEBUG:
                        if application_email and person.email:
                            subject = application_email.subject
                            from_email = application_email.sender
                            to_email = (person.email,)

                            try:
                                message_content = Template(application_email.content)
                                message = message_content.substitute(name=person.first_name)
                            except KeyError, e:
                                subject = "KeyError in application email"
                                message = "%s in application email id: %s" % (e.message, application_email.name)
                                mail_admins(subject, message)

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
                            subject = "%s %s for position %s has no email" % (person.first_name, person.last_name, job)
                            message = "%s %s (%s) does not have an email address. They applied for %s and were supposed to receive %s email." % (person.first_name, person.last_name, person.student_id, job, application_email.subject)
                            mail_admins(subject, message)
                            from_email = application_email.sender
                            to_email = (application_email.sender, )
                            email = EmailMessage(subject, message, from_email, to_email)
                            email.send()
                            comment = "%s no email could be sent" % (form.cleaned_data["status"])
                            user = request.user or None
                            content_type = ContentType.objects.get(name="application")
                            Comment.objects.create(content_type=content_type,
                                                    object_pk=application.id,
                                                    site=Site.objects.get_current(),
                                                    user=user,
                                                    comment=comment)
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
            return HttpResponse(content="401 Unauthorized: Access is denied due to invalid credentials.",
                                mimetype="text/plain", status=401)

    # TODO: change applicant_slug to username for clarity
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
def export_application(request, job_slug):
    job = get_object_or_404(Job.objects.all(), slug=job_slug)
    try:
        administrator = JobUser.objects.get(user=request.user, job=job)
    except JobUser.DoesNotExist:
        if not request.user.is_superuser:
            return HttpResponse(status=401, content="401 Unauthorized Access", mimetype="text/plain")

    response = HttpResponse(mimetype="text/csv")
    response["Content-Disposition"] = 'attachment; filename=%s_applications.csv' % job_slug
    writer = csv.writer(response)
    #create column headers
    columns = []
    for component in job.component_set.all():
        for component_part in component.componentpart_set.all():
            part_name = component_part.content_object.short_name or component_part.content_object.question
            column_name = "%s: %s" % (component, part_name)
            columns.append(column_name)
    writer.writerow(columns)

    # fill the rows with application component part responses
    for application in job.application_set.all():
        #only include submitted applications
        if application.is_submitted:
            component_responses = []
            application_component_parts = application.component_parts.all().order_by('component', 'sequence_number')

            for component_part in application_component_parts:
                component_response = application.applicationcomponentpart_set.get(
                                                                    application=application,
                                                                    component_part=component_part
                                                                    )
                if not component_response.content_type:
                    component_responses.append("empty")
                elif component_response.content_type.name == "file response":
                    component_responses.append( component_response.content_object.file.name)
                elif component_response.content_type.name == "boolean response":
                    component_responses.append( component_response.content_object.response)
                elif component_response.content_type.name == "work history response":
                    employer = component_response.content_object.employer
                    position_title = component_response.content_object.position_title
                    start_date = component_response.content_object.start_date
                    end_date = component_response.content_object.end_date
                    hours_worked = component_response.content_object.hours_worked
                    position_summary = component_response.content_object.position_summary
                    work_history = "Employer: %s, Position: %s, Start Date: %s, End Date: %s, Hours Worked: %s, Position Summary: %s " % (employer, position_title, start_date, end_date, hours_worked, position_summary)
                    component_responses.append(work_history.encode('ascii', 'ignore'))
                elif component_response.content_type.name == "placement preference response":
                    preference_responses = component_response.content_object.preferences.all()
                    preference_choices = "Preferences:"
                    for preference in preference_responses:
                        preference_choices  = "%s %s" %(preference_choices, preference)
                    preference_choices = "%s Explantion: %s" %(preference_choices,
                                                            component_response.content_object.explanation)

                    component_responses.append(preference_choices.encode('ascii', 'ignore'))
                else:
                    component_responses.append( component_response.content_object.response.encode('ascii', 'ignore'))
            writer.writerow(component_responses)

    return response


@login_required
def application(request, job_slug):
    job = Job.objects.get(slug=job_slug)
    #redirect if job closed
    if job.close_datetime < datetime.datetime.now():
        return HttpResponseRedirect(reverse("jobs_index"))

    #Chunks titled "jobs.job-slug-here-application-view" contain a message
    # to be displayed on the application view.
    chunk_key = "jobs-" + job.slug + "-application-view"
    try:
        chunk = Chunk.objects.get(key=chunk_key)
    except Chunk.DoesNotExist:
        chunk = None

    application_exists = Application.objects.filter(
        job=job,
        applicant__user=request.user
    ).count() > 0

    # Redirect the user to the job's website if the job isn't open
    # and they do not have an application
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
    if created:
        status = ApplicationStatus.objects.get(status="In Progress")
        AdminApplication.objects.create(application=application, status=status)

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

            status = ApplicationStatus.objects.get(status="Submitted")
            application_status = AdminApplication.objects.get(application=application)
            application_status.status = status
            application_status.save()

            message = u"<strong>Congratulations!</strong> Your application was successfully submitted."
            messages.success(request, message)
        else:
            message = u"<strong>Your application was not submitted.</strong> Please complete your application before submitting it."
            messages.error(request, message)

    context = {
        "application": application,
        "job": job,
        "chunk": chunk,
    }
    if job.deadline > datetime.datetime.now():
        context["submit"] = True

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

    context = {
        "application": application,
         "component": component,
         "component_parts": component_parts,
         "has_file_field": has_file_field
    }

    if job.deadline > datetime.datetime.now():
        context["modify"] = True

    return render_to_response(
        "jobs/component.html",
        context,
        context_instance=RequestContext(request)
    )



