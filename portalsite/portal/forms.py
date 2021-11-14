from django import forms


class MeasurementUploadForm(forms.Form):
    def __init__(self, type_choices: list, source_choices: list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['data_type'].choices = type_choices
        self.fields['source'].choices = source_choices

    measurement_time = forms.DateTimeField()
    data_type = forms.ChoiceField()
    source = forms.ChoiceField()
    file = forms.FileField(required=False)
