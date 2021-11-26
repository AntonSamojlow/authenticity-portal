from django import forms
from django.db.models.base import Model



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


class MeasurementScoreForm(forms.Form):
    def __init__(self, model_choices: list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['model'].choices = model_choices

    model = forms.ChoiceField()
