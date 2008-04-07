import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import Template, RequestContext, Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from wwu_housing.jobs.models import Applicant, Application
from wwu_housing.library.models import Address, AddressType, Phone, PhoneType
from wwu_housing.library.forms import AddressForm, PhoneForm
from wwu_housing.keymanager.models import Community
from forms import AvailabilityForm, ReferenceForm, PlacementPreferenceForm, EssayResponseForm
from models import EssayQuestion, PlacementPreference


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

    return render_to_response('desk_attendant/index.html', context, context_instance=RequestContext(request))


@login_required
def apply(request, job):
    """
    Displays the application form for a desk attendant applicant
    """
    # TODO: This is a job for students only, at what point should we check that attribute?


    # If the job is not open, forward to the index page
    #raise Exception("Job is open == %s" % job.is_open())
    #TODO: Remove "and False" when ready to be live
    if not job.is_open() and False:
        request.user.message_set.create(message="You cannot access the application site when the application is closed.")
        return HttpResponseRedirect(reverse('wwu_housing.jobs.desk_attendant.views.index'))

    # Try to load Applicant instance for request user using Applicant.objects.get_or_create().
    try:
        applicant, created = Applicant.objects.get_or_create(user=request.user)
    except Exception, e:
        raise Exception("couldn't create applicant: %s" % e)
        #TODO
        pass

    # Try to load Application instance for Applicant and Job (possibly by using Application.objects.get_or_create()).
    application, created = Application.objects.get_or_create(applicant=applicant, job=job)

    # If Application was created, display application forms.

    NUMBER_OF_REFERENCE_FORMS = 3
    data = request.POST or None
    context = {}

    if request.method == "POST":
        save_forms = True
        forms = []
    else:
        save_forms = False

    # Create address forms
    try:
        current_address_type = AddressType.objects.get(type='current')
        current_address, created = Address.objects.get_or_create(address_type=current_address_type, user=request.user)
    except Exception, e:
        raise Exception("Failed to create address: %s" % e)
    try:
        summer_address_type = AddressType.objects.get(type='summer')
        summer_address, created = Address.objects.get_or_create(address_type=summer_address_type, user=request.user)
    except Exception, e:
        raise Exception("Failed to create address: %s" % e)

    # Create phone forms
    try:
        current_phone_type = PhoneType.objects.get(type='current')
        current_phone, created = Phone.objects.get_or_create(phone_type=current_phone_type, user=request.user)
    except Exception, e:
        raise Exception("Failed to create phone: %s" % e)
    try:
        summer_phone_type = PhoneType.objects.get(type='summer')
        summer_phone, created = Phone.objects.get_or_create(phone_type=summer_phone_type, user=request.user)
    except Exception, e:
        raise Exception("Failed to create phone: %s" % e)
    try:
        cell_phone_type = PhoneType.objects.get(type='cell')
        cell_phone, created = Phone.objects.get_or_create(phone_type=cell_phone_type, user=request.user)
    except Exception, e:
        raise Exception("Failed to create phone: %s" % e)

    # Generate a form for each essay question
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

    # Generate each reference form
    context['reference_forms'] = []
    for i in xrange(NUMBER_OF_REFERENCE_FORMS):
        reference_subform = ReferenceForm(data, prefix=i)
        if request.method == 'POST' and reference_subform.is_valid():
            if len([field for field in reference_subform.cleaned_data.values() if i is not None]) > 0:
                forms.append(reference_subform)
        elif reference_subform.errors:
            save_forms = False
        context['reference_forms'].append(reference_subform)

    # Check availability form for validity and save if needed
    availability_form = AvailabilityForm(data)
    if request.method == 'POST' and availability_form.is_valid():
        forms.append(availability_form)
    elif availability_form.errors:
        save_forms = False
    context['availability_form'] = availability_form

    # Check whether forms can be saved.
    if save_forms:
        for form in forms:
            # Before saving the forms, the application must be set for each form instance
            # and any required elements must also be set.
            instance = form.save(commit=False)
            instance.application = application
            if isinstance(form, PlacementPreferenceForm):
                instance.community = form.community
            elif isinstance(form, EssayResponseForm):
                instance.question = form.question
            instance.save()
        request.user.message_set.create(message="Your application was submitted successfully!")
        return HttpResponseRedirect(reverse('wwu_housing.jobs.desk_attendant.views.index'))

    context['current_address_form'] = AddressForm(instance=current_address)
    context['summer_address_form'] = AddressForm(instance=summer_address)
    context['current_phone_form'] = PhoneForm(instance=current_phone)
    context['summer_phone_form'] = PhoneForm(instance=summer_phone)
    context['cell_phone_form'] = PhoneForm(instance=cell_phone)
    context['application'] = application
    context['job'] = job
    return render_to_response('desk_attendant/apply.html', context, context_instance=RequestContext(request))
