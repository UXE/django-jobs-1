from django import newforms as forms

from models import Availability, Reference, PlacementPreference, EssayResponse


class AvailabilityForm(forms.ModelForm):
    hours_available = forms.IntegerField(min_value=1, max_value=19, help_text='Please use a whole number from one to nineteen.')

    class Meta:
        model = Availability
        exclude = ('application',)


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        exclude = ('application',)

    def clean(self):
        # We require either both fields filled out or neither
        if (len(self.cleaned_data.get('name', '')) > 0 and len(self.cleaned_data.get('phone', '')) == 0) or (len(self.cleaned_data.get('name', '')) == 0 and len(self.cleaned_data.get('phone', '')) > 0):
            raise forms.ValidationError('You must either leave both fields blank for a given reference or fill out both fields')
        else:
            return self.cleaned_data


class PlacementPreferenceForm(forms.ModelForm):
    rank = forms.CharField(required=False,
                           widget=forms.TextInput(attrs={'size': 3, 'maxsize': 3}))

    class Meta:
        model = PlacementPreference
        fields = ('rank',)


class EssayResponseForm(forms.ModelForm):
    class Meta:
        model = EssayResponse
        fields = ('answer',)
