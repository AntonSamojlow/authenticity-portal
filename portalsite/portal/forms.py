from typing import TYPE_CHECKING
from django import forms
from django.forms.widgets import Textarea

class MeasurementUploadForm(forms.Form):
    def __init__(self, 
    data_handler_choices: list, 
    source_choices: list,
    groups_choices: list,
    *args, 
    **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['data_handler'].choices = data_handler_choices
        self.fields['source'].choices = source_choices
        self.fields['groups'].choices = groups_choices

    measured = forms.DateTimeField()
    name = forms.CharField(max_length=50, required=True)
    data_handler = forms.ChoiceField()
    source = forms.ChoiceField()
    groups = forms.MultipleChoiceField(required=False)
    file = forms.FileField(required=False)
    notes = forms.CharField(required=False, widget=Textarea)

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

class NewSimcaModelForm(forms.Form):
    def __init__(self, limit_type_choices: list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['limit_type'].choices = limit_type_choices

    name = forms.CharField(required=True)
    features = forms.IntegerField(min_value=2, required=True)  
    components = forms.IntegerField(min_value=1, required=True)  
    alpha = forms.FloatField(min_value=0, max_value=1, initial=0.05, required=True)  
    gamma = forms.FloatField(min_value=0, max_value=1, initial=0.01, required=True)  
    limit_type = forms.ChoiceField()  
    scale = forms.BooleanField(required=False, initial=False)  

class CopyModelForm(forms.Form):
    new_name = forms.CharField(required=True)
