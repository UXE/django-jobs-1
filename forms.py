from django import forms

from models import AdminApplication, ApplicationStatus

class AdminApplicationForm(forms.ModelForm):
    status = forms.ModelChoiceField(queryset=ApplicationStatus.objects.all(), label="", empty_label=None)
    class Meta:
        fields = ("status",)
        model = AdminApplication
