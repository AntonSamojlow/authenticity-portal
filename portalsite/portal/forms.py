from django import forms
from portal.models import Measurement

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


class MeasurementPredictForm(forms.Form):
    def __init__(self, model_choices: list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['model'].choices = model_choices

    model = forms.ChoiceField(required=True)
  

class ModelTrainForm(forms.Form):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @staticmethod
    def _get_query_set():
        return Measurement.objects.all()

    name = forms.CharField(required=False,
        help_text="Name of the resulting trained model - leave blank to *update* the current model")
    measurements = forms.ModelMultipleChoiceField(queryset=_get_query_set())
