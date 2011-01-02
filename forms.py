from django import forms

from models import AdminApplication, ApplicationStatus

class AdminApplicationForm(forms.ModelForm):
    """
        Change the application status
    """
    queryset = ApplicationStatus.objects.order_by("weight")
    status = forms.ModelChoiceField(queryset=queryset,
                                    label="",
                                    empty_label=None)

    class Meta:
        fields = ("status",)
        model = AdminApplication
