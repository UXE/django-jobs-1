from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import Template, RequestContext, Context, loader
from django.http import HttpResponse
#from wwu_housing.jobs.models import Job
from wwu_housing.keymanager.models import Community
from forms import AvailabilityForm, ReferenceForm, PlacementPreferenceForm, EssayResponseForm
from models import EssayQuestion, PlacementPreference
from datetime import datetime

def index(request, job):
    """
    Basic info page that tells about the desk attendant application
    """
    t = loader.get_template('desk_attendant/index.html')
    c = Context({'job': job})
    return HttpResponse(t.render(c))

@login_required
def apply(request, job):
    """
    Displays the application form for a desk attendant applicant
    """
    # TODO: This is a job for students only, at what point should we check that attribute?


    # If the job is not yet opened, display a message and exit.
    if datetime.now() < job.open_datetime:
        #TODO
        pass

    # If the job close date has passed, display a message and exit.
    if datetime.now() > job.close_datetime:
        #TODO
        pass

    # If the job deadline has passed, display a message and exit.
    if datetime.now() > job.deadline:
        #TODO
        pass

    # Try to load Applicant instance for request user using jobs.Applicant.objects.get_or_create().
    try:
        applicant = jobs.Applicant.objects.get_or_create()
    except:
        #ah, crud
        #TODO
        pass

    # Try to load Application instance for Applicant and Job (possibly by using jobs.Application.objects.get_or_create()).
    try:
        application = jobs.Application.objects.get_or_create()
    except:
        # If Application was not created, display message or redirect user and exit.
        #ah, crud #2
        #TODO
        pass

    # If Application was created, display application forms.

    NUMBER_OF_REFERENCE_FORMS = 3
    data = request.POST or None
    context = {}

    # Generate a form for each essay question
    questions = EssayQuestion.objects.all()
    context['essay_response_form'] = []
    for question in questions:
        essay_response_subform = EssayResponseForm(data, initial={'question': question.question}, prefix=question.id)
        if request.method == 'POST' and essay_response_subform.is_valid():
            essay_response_subform.save()
        essay_response_subform.prompt = question
        context['essay_response_form'].append(essay_response_subform)

    # Generate a form for each placement preference (community)
    context['placement_preference_form'] = []
    for community in Community.objects.all():
        placement_preference_subform = PlacementPreferenceForm(data, initial={'community': community.name}, prefix=community.id)
        if request.method == 'POST' and placement_preference_subform.is_valid():
            placement_preference_subform.save()
        placement_preference_subform.name = community.name
        context['placement_preference_form'].append(placement_preference_subform)

    # Generate each reference form
    context['reference_forms'] = []
    for i in xrange(1, NUMBER_OF_REFERENCE_FORMS+1):
        reference_subform = ReferenceForm(data, prefix=i)
        if request == 'POST' and reference_subform.is_valid():
            reference_subform.save()
        context['reference_forms'].append(reference_subform)

    # Check availability form for validity and save if needed
    if request == 'POST' and AvailabilityForm(data).is_valid():
        AvailabilityForm(data).save();

    # Add the easy one and render
    context['availability_form'] = AvailabilityForm(data)
    context['job'] = job
    return render_to_response('desk_attendant/applicant/index.html', context, context_instance=RequestContext(request))
