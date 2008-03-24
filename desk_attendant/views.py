from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from forms import AvailabilityForm, ReferenceForm, PlacementPreferenceForm, EssayResponseForm

@login_required
def index(request):
    """
    Displays the application form for a desk attendant applicant
    """
    data = request.POST or None
    availability_form = AvailabilityForm(data)
    reference_form1 = ReferenceForm(data)
    reference_form2 = ReferenceForm(data)
    reference_form3 = ReferenceForm(data)
    placement_preference_form = PlacementPreferenceForm(data)
    essay_response_form = EssayResponseForm(data)

    return render_to_response('desk_attendant/applicant/index.html', {
                              'availability_form': availability_form,
                              'reference_form1': reference_form1,
                              'reference_form2': reference_form2,
                              'reference_form3': reference_form3,
                              'placement_preference_form': placement_preference_form, 
                              'essay_response_form': essay_response_form,
                              }, context_instance=RequestContext(request))
