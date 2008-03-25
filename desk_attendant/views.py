from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import Template, RequestContext, Context
from forms import AvailabilityForm, ReferenceForm, PlacementPreferenceForm, EssayResponseForm
from models import EssayQuestion, PlacementPreference
from wwu_housing.keymanager.models import Community

@login_required
def index(request):
    """
    Displays the application form for a desk attendant applicant
    """
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
        subform = ReferenceForm(data, prefix=1)
        if request == 'POST' and subform.is_valid():
            subform.save()
        context['reference_forms'].append(subform)

    # Add the easy one and render
    context['availability_form'] = AvailabilityForm(data)
    return render_to_response('desk_attendant/applicant/index.html', context)