from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    """
    Displays the application form for a desk attendant applicant
    """
    data = request.POST or None
