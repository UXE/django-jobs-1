from django import newforms as forms
from models import Availability, Reference, PlacementPreference, EssayResponse


class AvailabilityForm(forms.ModelForm):
    hours_available = forms.IntegerField(min_value=1, max_value=19)
    class Meta:
        model = Availability


class ReferenceForm(forms.ModelForm):
    def clean(self):
        # We require either both fields filled out or neither
        if (len(self.cleaned_data.get('name')) > 0 and len(self.cleaned_data.get('phone')) == 0) or (len(self.cleaned_data.get('name')) == 0 and len(self.cleaned_data.get('phone')) > 0):
            raise forms.ValidationError('You must either leave both fields blank for a given reference or fill out both fields')
        else:
            return self.cleaned_data
    class Meta:
        model = Reference


class PlacementPreferenceForm(forms.ModelForm):
    class Meta:
        model = PlacementPreference


class EssayResponseForm(forms.ModelForm):
    class Meta:
        model = EssayResponse
