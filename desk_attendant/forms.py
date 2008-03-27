from django import newforms as forms
from models import Availability, Reference, PlacementPreference, EssayResponse


class AvailabilityForm(forms.ModelForm):
    hours_available = forms.IntegerField(min_value=1, max_value=19)
    class Meta:
        model = Availability


class ReferenceForm(forms.ModelForm):
    def clean(self):
        try:
            if (len(self.name) > 0 and len(self.phone) == 0) or (len(self.name) == 0 and len(self.phone) > 0):
                raise forms.ValidationError('You must either leave both fields blank for a given reference or fill out both fields')
            else:
                #TODO: do validation?  We need to decide on how to represent phone numbers and what constitues a phone number
                #TODO: clean data?
                #return dict of clean values... don't know if I did this right...
                return {'name': self.name, 'phone': self.phone}
        except:
            raise forms.ValidationError('You must either leave both fields blank for a given reference or fill out both fields')
            pass # should do something? but 

    class Meta:
        model = Reference


class PlacementPreferenceForm(forms.ModelForm):
    class Meta:
        model = PlacementPreference


class EssayResponseForm(forms.ModelForm):
    class Meta:
        model = EssayResponse
