from typing import TYPE_CHECKING
from django import forms

class MeasurementUploadForm(forms.Form):
    def __init__(self, data_handler_choices: list, source_choices: list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['data_handler'].choices = data_handler_choices
        self.fields['source'].choices = source_choices

    measured = forms.DateTimeField()
    name = forms.CharField(max_length=50, required=True)
    data_handler = forms.ChoiceField()
    source = forms.ChoiceField()
    file = forms.FileField(required=False)

class FilterForm(forms.Form):
    ALL = 'ALL'
    filter = forms.ChoiceField(required=True)
    def __init__(self, name:str, label:str, choices: list, initial: str = None, includeAll =False, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Hack to allow several filters in same view (the POST request returns the variable name, currently 'filter')
        self.fields[name] = self.fields['filter']
        del self.fields['filter']
        
        if initial is not None:
            self.fields[name].initial = initial

        self.fields[name].label = label
        self.fields[name].choices = ([(self.ALL,self.ALL)] if includeAll else []) + choices


class ModelTrainForm(forms.Form):
    name = forms.CharField(required=False,
        help_text="Name of the resulting trained model - leave blank to *update* the current model")
    measurements = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, measurement_query_set, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['measurements'].queryset = measurement_query_set
   

class NewLinearRegssionModelForm(forms.Form):
    name = forms.CharField(required=True)
    features = forms.IntegerField(min_value=1, required=True)

class NewTestModelForm(forms.Form):
    name = forms.CharField(required=True)

class CopyModelForm(forms.Form):
    new_name = forms.CharField(required=True)
