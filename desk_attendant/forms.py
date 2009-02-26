from django import forms

from models import Availability, Reference, PlacementPreference, EssayResponse, Resume, ApplicantStatus


class HoursHiredForForm(forms.ModelForm):
    name = "hours_hired_for"
    value = forms.IntegerField(max_value=19, min_value=0, initial=0)

    class Meta:
        fields = ("value",)
        model = ApplicantStatus

class ProcessStatusForm(forms.ModelForm):
    STATUS_CHOICES = (
        ("unreviewed", "Unreviewed"),
        ("reviewed", "Reviewed"),
        ("scheduled_interview", "Scheduled Interview"),
        ("interviewed", "Interviewed"),
        ("hired", "Hired"),
        ("not_considered", "Not Considered"),
    )
    name = "process_status"
    value = forms.CharField(max_length=50,
                    widget=forms.Select(choices=STATUS_CHOICES))

    class Meta:
        fields = ("value",)
        model = ApplicantStatus

class AvailabilityForm(forms.ModelForm):
    ON_CAMPUS_CHOICES = (
        ("unknown", "I Don't Know"),
        ("yes", "Yes"),
        ("no", "No"),
    )
    WORK_STUDY_CHOICES = (
        ("unknown", "I Don't Know"),
        ("yes", "Yes"),
        ("no", "No"),
    )
    RETURNING_DA_CHOICES = (
        ("yes", "Yes"),
        ("no", "No"),
    )
    hours_available = forms.IntegerField(min_value=1, max_value=19, help_text="Please use a whole number from one to nineteen.")
    on_campus = forms.CharField(label=Availability._meta.get_field_by_name("on_campus")[0].verbose_name,
                                widget=forms.RadioSelect(choices=ON_CAMPUS_CHOICES),
                                initial=ON_CAMPUS_CHOICES[0][0])
    work_study = forms.CharField(label=Availability._meta.get_field_by_name("work_study")[0].verbose_name,
                                widget=forms.RadioSelect(choices=WORK_STUDY_CHOICES),
                                initial=WORK_STUDY_CHOICES[0][0])
    prior_desk_attendant = forms.CharField(label=Availability._meta.get_field_by_name("prior_desk_attendant")[0].verbose_name,
                                        widget=forms.RadioSelect(choices=RETURNING_DA_CHOICES))

    class Meta:
        model = Availability
        exclude = ("application",)


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        exclude = ("application",)

    def clean(self):
        # We require either both fields filled out or neither
        if (len(self.cleaned_data.get("name", "")) > 0 and len(self.cleaned_data.get("phone", "")) == 0) or (len(self.cleaned_data.get("name", "")) == 0 and len(self.cleaned_data.get("phone", "")) > 0):
            raise forms.ValidationError("You must either leave both fields blank for a given reference or fill out both fields")
        else:
            return self.cleaned_data


class PlacementPreferenceForm(forms.ModelForm):
    rank = forms.CharField(required=False,
                           widget=forms.TextInput(attrs={"size": 3, "maxsize": 3}))

    class Meta:
        model = PlacementPreference
        fields = ("rank",)


class EssayResponseForm(forms.ModelForm):
    class Meta:
        model = EssayResponse
        fields = ("answer",)

    def clean_answer(self):
        cleaned_answer = self.cleaned_data["answer"].strip()
        if not cleaned_answer:
            raise forms.ValidationError("This field is required.")
        return cleaned_answer


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ("resume",)
