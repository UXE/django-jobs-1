import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Template, RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from wwu_housing.jobs.models import Applicant, Application
from wwu_housing.library.models import Address, AddressType, Phone, PhoneType
from wwu_housing.library.forms import AddressForm, PhoneForm
from wwu_housing.keymanager.models import Community
from forms import AvailabilityForm, ReferenceForm, PlacementPreferenceForm, EssayResponseForm, ResumeForm
from models import EssayQuestion, PlacementPreference, ApplicantStatus, Availability


def index(request, job):
    """
    Basic info page that tells about the desk attendant application
    """
    # TODO: This could probably use a generic view.
    context = {'job': job}
    try:
        applicant, created = Applicant.objects.get_or_create(user=request.user)
    except:
        applicant = False

    try:
        application, created = Application.objects.get(applicant=applicant)
    except:
        application = False

    # Handle application messages from the session
    try:
        context['da_message'] = request.session['da_message']
        del request.session['da_message']
    except:
        pass

    return render_to_response('desk_attendant/index.html', context, context_instance=RequestContext(request))


@login_required
def apply(request, job):
    """
    Displays the application form for a desk attendant applicant
    """
    # TODO: This is a job for students only, at what point should we check that attribute?

    # If the job is not open, forward to the index page
    if not job.is_open():
        request.session['da_message'] = 'You cannot access the application site when the application is closed.'
        return HttpResponseRedirect(reverse('wwu_housing.jobs.desk_attendant.views.index'))

    # Try to load Applicant instance for request user using Applicant.objects.get_or_create().
    applicant, created = Applicant.objects.get_or_create(user=request.user)

    # Try to load Application instance for Applicant and Job (possibly by using Application.objects.get_or_create()).
    application, created = Application.objects.get_or_create(applicant=applicant, job=job)

    # If the applicant has already submitted their application, redirect them to the index.
    if application.end_datetime:
        request.session['da_message'] = "You have already submitted your application.  Please contact Residence Life at 650-2960 or by email at reslife@wwu.edu if you have any questions about your application."
        return HttpResponseRedirect(reverse('wwu_housing.jobs.desk_attendant.views.index'))

    # If Application was created, display application forms.
    NUMBER_OF_REFERENCE_FORMS = 3
    data = request.POST or None
    files = request.FILES or None
    context = {}

    if request.method == "POST":
        save_forms = True
        forms = []
    else:
        save_forms = False

    address_defaults = {}
    phone_defaults = {}
    if hasattr(request.user, 'student'):
        address = request.user.student.mailing_address
        if address:
            address_defaults['current'] = {'street_line_1': address.street_line1,
                                           'street_line_2': address.street_line2,
                                           'street_line_3': address.street_line3,
                                           'city': address.city,
                                           'district': address.state,
                                           'zip': address.zip}
            if address.phone_number:
                phone_defaults['current'] = {'phone': "%s-%s-%s" % (address.area_code, 
                                                                    address.phone_number[:3],
                                                                    address.phone_number[3:])}

    # Generate a form for each address type.
    address_types = ('current', 'summer')
    for address_type in address_types:
        address_type_instance = AddressType.objects.get(type=address_type)
        address, created = Address.objects.get_or_create(address_type=address_type_instance, user=request.user,
                                                         defaults=address_defaults.get(address_type, {}))
        address_form = AddressForm(data, instance=address, prefix="%s-address" % address_type)
        if address_form.is_valid():
            forms.append(address_form)
        elif address_form.errors:
            save_forms = False
        context['%s_address_form' % address_type] = address_form

    # Generate a form for each phone type.
    phone_types = ('current', 'summer', 'cell')
    for phone_type in phone_types:
        phone_type_instance = PhoneType.objects.get(type=phone_type)
        phone, created = Phone.objects.get_or_create(phone_type=phone_type_instance, user=request.user,
                                                     defaults=phone_defaults.get(phone_type, {}))
        phone_form = PhoneForm(data, instance=phone, prefix="%s-phone" % phone_type)

        # Make cell phone unrequired.
        if phone_type == 'cell':
            phone_form.fields['phone'].required = False

        if phone_form.is_valid():
            forms.append(phone_form)
        elif phone_form.errors:
            save_forms = False
        context['%s_phone_form' % phone_type] = phone_form

    # Generate a form for each essay question.
    questions = EssayQuestion.objects.all()
    context['essay_response_forms'] = []
    for question in questions:
        essay_response_subform = EssayResponseForm(data, prefix=question.id)
        if request.method == 'POST' and essay_response_subform.is_valid():
            if essay_response_subform.cleaned_data['answer']:
                forms.append(essay_response_subform)
        elif essay_response_subform.errors:
            save_forms = False
        essay_response_subform.question = question
        context['essay_response_forms'].append(essay_response_subform)

    # Generate a form for each placement preference (community).
    context['placement_preference_forms'] = []
    for community in Community.objects.all():
        placement_preference_subform = PlacementPreferenceForm(data, prefix=community.id)
        if request.method == 'POST' and placement_preference_subform.is_valid():
            # The form may be valid, but we only want to save forms with ranks.
            if placement_preference_subform.cleaned_data['rank']:
                forms.append(placement_preference_subform)
        elif placement_preference_subform.errors:
            save_forms = False
        placement_preference_subform.community = community
        context['placement_preference_forms'].append(placement_preference_subform)

    # Generate each reference form.
    context['reference_forms'] = []
    for i in xrange(NUMBER_OF_REFERENCE_FORMS):
        reference_subform = ReferenceForm(data, prefix=i)

        # Make the first reference required.  
        # TODO: How would we specify this dynamically for app^2?
        if i == 0:
            reference_subform.fields['name'].required = True
            reference_subform.fields['phone'].required = True

        if request.method == 'POST' and reference_subform.is_valid():
            if len([field for field in reference_subform.cleaned_data.values() if field]) > 0:
                forms.append(reference_subform)
        elif reference_subform.errors:
            save_forms = False
        context['reference_forms'].append(reference_subform)

    # Check availability form for validity and save if needed.
    availability_form = AvailabilityForm(data)
    if request.method == 'POST' and availability_form.is_valid():
        forms.append(availability_form)
    elif availability_form.errors:
        save_forms = False
    context['availability_form'] = availability_form

    resume_form = ResumeForm(data, files)
    resume_form.fields['resume'].required = False
    if request.method == 'POST' and resume_form.is_valid():
        forms.append(resume_form)
    elif resume_form.errors:
        save_forms = False
    context['resume_form'] = resume_form

    # Check whether forms can be saved.
    if save_forms:
        for form in forms:
            # Resumes need pre-processing: each resume needs a unique filename per application.
            if isinstance(form, ResumeForm):
                # Try to get a file extension and use the application id as the new filename.
                if not form.cleaned_data['resume']:
                    continue
                filename_pieces = form.cleaned_data['resume'].filename.split('.')
                if len(filename_pieces) > 1:
                    extension = filename_pieces[-1]
                    filename = "%i.%s" % (application.id, extension)
                else:
                    filename = "%i.txt" % application.id
                # Use the application id to uniquely identify the resume file.
                form.cleaned_data['resume'].filename = filename

            # Before saving the forms, the application must be set for each form instance
            # and any required elements must also be set.
            instance = form.save(commit=False)
            instance.application = application
            if isinstance(form, PlacementPreferenceForm):
                instance.community = form.community
            elif isinstance(form, EssayResponseForm):
                instance.question = form.question
            elif isinstance(form, AddressForm) or isinstance(form, PhoneForm):
                instance.user = applicant.user
            instance.save()

        # Close out the application by adding an end datetime
        application.end_datetime = datetime.datetime.now()
        application.save()
        request.session['da_message'] = 'Your application was submitted successfully!'
        return HttpResponseRedirect(reverse('wwu_housing.jobs.desk_attendant.views.index'))

    context['application'] = application
    context['job'] = job

    return render_to_response('desk_attendant/apply.html', context, context_instance=RequestContext(request))

@login_required
def admin(request, job, id=None):
    """Routes admin to list or individual views"""
    # TODO: Is user authorized to view admin page?
    # if request.user.has_perm('view_da_stuff')
    # if staff or if in group rd
    if request.user.is_staff:
        pass

    if (id is None):
        return admin_list(request, job)
    else:
        return admin_individual(request, job, id)

def admin_individual(request, job, id):
    """Allows RDs to view individual applications for their communities and
    set statuses"""
    app = get_object_or_404(Application, pk=id)

    # Build context
    context = {}
    context['job'] = job
    context['application'] = app
    context['applicant'] = app.applicant.user.get_full_name()
    context['addresses'] = app.applicant.user.address_set.all()
    context['phones'] = app.applicant.user.phone_set.all()
    context['references'] = app.reference_set.all()
    context['placement_preferences'] = app.placementpreference_set.all()
    context['essay_responses'] = app.essayresponse_set.all()

    try:
        context['availability'] = app.availability_set.all()[0]
    except:
        context['availability'] = False

    return render_to_response('desk_attendant/admin.html', context, context_instance=RequestContext(request))

def admin_list(request, job):
    """Allows RDs to list the applications for easy viewing and sorting"""
    app_ids = Application.objects.filter(end_datetime__isnull=False).values('id')[0].values()
    availability = Availability.objects.filter(application__in=app_ids)
    # TODO add filter(community=123) to status obj
    status = ApplicantStatus.objects.filter(application__in=app_ids)
    apps = {}
    application = {}
    #availability_fields = {'Prior DA':'prior_desk_attendant', 'Hours Available':'hours_available'}

    for a in availability:
        apps[a.application_id] = {}
        apps[a.application_id]['Prior DA'] = a.prior_desk_attendant
        apps[a.application_id]['Hours Available'] = a.hours_available
        apps[a.application_id]['On Campus'] = a.on_campus
        apps[a.application_id]['Where on Campus'] = a.on_campus_where
        # Why can't I do the below?
        #for k, v in availability_fields.items():
            #apps[a.application_id][k] = a.v

    for s in status:
        apps[s.application_id][s.community]['name'] = s.name
        apps[s.application_id][s.community]['name'] = s.value

    # Below way won't work without 80 billion queries
    # Build exactly what we need from apps to pass to view
    # TODO: Make beautiful....
    #for app in app_ids:
        #application['Prior DA'] = availability.filter(application=app).

        #application['name'] = app.applicant
        # The next line is ugly; what's a better way?
        #application['prior desk attendant'] = app.availability_set.values('prior_desk_attendant')[0]['prior_desk_attendant']
        #application['hours available'] = app.availability_set.values('hours_available')[0]['hours_available']
        #application['will live on campus'] = app.availability_set.values('on_campus')[0]['on_campus']
        #application['living next year'] = app.availability_set.values('on_campus_where')[0]['on_campus_where']
        #apps_modified.append(application)
        #del application

    #raise Exception(apps)
    context = {}
    context['applications'] = apps
    context['job'] = job
    context['total_applications'] = len(apps)

    return render_to_response('desk_attendant/adminlist.html', context, context_instance=RequestContext(request))
