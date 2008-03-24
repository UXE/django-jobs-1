from django import newforms as forms
from models import Availability, Reference, PlacementPreference, EssayResponse


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference


class PlacementPreferenceForm(forms.ModelForm):
    class Meta:
        model = PlacementPreference


class EssayResponseForm(forms.ModelForm):
    class Meta:
        model = EssayResponse
