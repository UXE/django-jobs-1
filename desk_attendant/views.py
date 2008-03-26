from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import Template, RequestContext, Context
from wwu_housing import jobs
from wwu_housing.keymanager.models import Community
from forms import AvailabilityForm, ReferenceForm, PlacementPreferenceForm, EssayResponseForm
from models import EssayQuestion, PlacementPreference

@login_required
def index(request, job):
    """
    Displays the application form for a desk attendant applicant
    """
    # If the job close date has passed, display a message and exit.

    # If the job deadline has passed, display a message and exit.

    # Try to load Applicant instance for request user using jobs.Applicant.objects.get_or_create().

    # Try to load Application instance for Applicant and Job (possibly by using jobs.Application.objects.get_or_create()).

    # If Application was not created, display message or redirect user and exit.

    # If Application was created, display application forms.

    NUMBER_OF_REFERENCE_FORMS = 3
    data = request.POST or None
    context = {}

    # Generate a form for each essay question
    questions = EssayQuestion.objects.all()
    context['essay_response_form'] = []
    for question in questions:
        subform = EssayResponseForm(data, initial={'question': question.question}, prefix=question.id)
        if request.method == 'POST' and subform.is_valid():
            subform.save()
        subform.prompt = question
        context['essay_response_form'].append(subform)

    # Generate a form for each placement preference (community)
    context['placement_preference_form'] = []
    for community in Community.objects.all():
        subform = PlacementPreferenceForm(data, initial={'community': community.name}, prefix=community.id)
        if request.method == 'POST' and subform.is_valid():
            subform.save()
        subform.name = community.name
        context['placement_preference_form'].append(subform)

    # Generate each reference form
    context['reference_forms'] = []
    for i in xrange(1, NUMBER_OF_REFERENCE_FORMS+1):
        subform = ReferenceForm(data, prefix=i)
        if request == 'POST' and subform.is_valid():
            subform.save()
        context['reference_forms'].append(subform)

    # Add the easy one and render
    context['availability_form'] = AvailabilityForm(data)
    context['job'] = job
    return render_to_response('desk_attendant/applicant/index.html', context)
