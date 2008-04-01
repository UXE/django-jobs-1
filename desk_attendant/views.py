import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import Template, RequestContext, Context, loader
from django.http import HttpResponse
from wwu_housing.jobs.models import Applicant, Application
from wwu_housing.keymanager.models import Community
from forms import AvailabilityForm, ReferenceForm, PlacementPreferenceForm, EssayResponseForm
from models import EssayQuestion, PlacementPreference

def index(request, job):
    """
    Basic info page that tells about the desk attendant application
    """
    # TODO: This could probably use a generic view.
    context = {'job': job}
    return render_to_response('desk_attendant/index.html', context, context_instance=RequestContext(request))

@login_required
def apply(request, job):
    """
    Displays the application form for a desk attendant applicant
    """
    # TODO: This is a job for students only, at what point should we check that attribute?


    # If the job is not yet opened, display a message and exit.
    if datetime.datetime.now() < job.open_datetime:
        #TODO
        pass

    # If the job close date has passed, display a message and exit.
    if datetime.datetime.now() > job.close_datetime:
        #TODO
        pass

    # If the job deadline has passed, display a message and exit.
    if datetime.datetime.now() > job.deadline:
        #TODO
        pass

    # Try to load Applicant instance for request user using Applicant.objects.get_or_create().
    try:
        applicant = Applicant.objects.get_or_create(user=request.user)
    except:
        #raise Exception(help("crap"))
        #TODO
        pass

    # Try to load Application instance for Applicant and Job (possibly by using Application.objects.get_or_create()).
    try:
        pass
        #application = Application.objects.get_or_create(applicant=applicant, job=job, start_datetime=datetime.datetime.now())
    except:
        raise Exception("Oops")
        # If Application was not created, display message or redirect user and exit.
        #ah, crud #2
        #TODO
        pass

    # If Application was created, display application forms.

    NUMBER_OF_REFERENCE_FORMS = 3
    data = request.POST or None
    context = {}

    if request.method == "POST":
        save_forms = True
        forms = []
    else:
        save_forms = False

    # Generate a form for each essay question
    questions = EssayQuestion.objects.all()
    context['essay_response_forms'] = []
    for question in questions:
        essay_response_subform = EssayResponseForm(data, prefix=question.id)
        if request.method == 'POST' and essay_response_subform.is_valid():
            forms.append(essay_response_subform)
        elif essay_response_subform.errors:
            save_forms = False
        essay_response_subform.question = question
        context['essay_response_forms'].append(essay_response_subform)

    # Generate a form for each placement preference (community).
    context['placement_preference_form'] = []
    for community in Community.objects.all():
        placement_preference_subform = PlacementPreferenceForm(data, prefix=community.id)
        if request.method == 'POST' and placement_preference_subform.is_valid():
            forms.append(placement_preference_subform)
        elif placement_preference_subform.errors:
            save_forms = False
        placement_preference_subform.community = community
        context['placement_preference_form'].append(placement_preference_subform)

    # Generate each reference form
    context['reference_forms'] = []
    for i in xrange(NUMBER_OF_REFERENCE_FORMS):
        reference_subform = ReferenceForm(data, prefix=i)
        if request == 'POST' and reference_subform.is_valid():
            forms.append(reference_subform)
        elif reference_subform.errors:
            save_forms = False
        context['reference_forms'].append(reference_subform)

    # Check availability form for validity and save if needed
    availability_form = AvailabilityForm(data)
    if request == 'POST' and availability_form.is_valid():
        forms.append(availability_form)
    elif availability_form.errors:
        save_forms = False
    context['availability_form'] = availability_form

    # Check whether forms can be saved.
    if save_forms:
        #raise Exception("Saving forms!")
        for form in forms:
            if isinstance(form, PlacementPreferenceForm):
                if form.cleaned_data['rank']:
                    instance = form.save(commit=False)
                    instance.community = form.community
                    instance.save()
            elif isinstance(form, EssayResponseForm):
                instance = form.save(commit=False)
                instance.question = form.question
                instance.save()
            else:
                form.save()

    # TODO: If forms were saved successfully, let the user know

    context['job'] = job
    return render_to_response('desk_attendant/apply.html', context, context_instance=RequestContext(request))
