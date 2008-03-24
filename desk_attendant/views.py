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

    return render_to_response('desk_attendant/applicant/index.html', 
                              {'availability_form': availability_form,}, 
                              context_instance=RequestContext(request))
