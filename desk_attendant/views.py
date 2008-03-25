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
        if request.method == 'POST' and form.is_valid() and subform.is_valid():
            EssayResponse(question_id=question.id).save()
        else:
            form_complete = False # TODO
        subform.prompt = question
        context['essay_response_form'].append(subform)

    # Generate a form for each placement preference (community)
    context['placement_preference_form'] = []
    for community in Community.objects.all():
        subform = PlacementPreferenceForm(data, initial={'community': community.name}, prefix=community.id)
        if request.method == 'POST' and form.is_valid() and subform.is_valid():
            PlacementPreference(community_id=community.id).save()
        else:
            form_complete = False # TODO
        subform.name = community.name
        context['placement_preference_form'].append(subform)

    # Generate each reference form
    context['reference_forms'] = []
    for i in xrange(1, NUMBER_OF_REFERENCE_FORMS+1):
        context['reference_forms'].append(ReferenceForm(data, prefix=i))
        pass

    context['availability_form'] = AvailabilityForm(data)
    #context['reference_form1'] = ReferenceForm(data)
    #context['reference_form2'] = ReferenceForm(data)
    #context['reference_form3'] = ReferenceForm(data)
    #context['placement_preference_form'] = PlacementPreferenceForm(data)
    
    return render_to_response('desk_attendant/applicant/index.html', context)
