from datetime import datetime
from django.core import files
from django.core.files.uploadedfile import UploadedFile
from django.http.request import HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from portal.forms import MeasurementUploadForm
from portal.models import MeasurementDataType, Measurement, Source
from .dataimport.csvparser import CsvParser

@login_required
def index(request: HttpRequest):

    date_time_format = "%d-%m-%Y, %H:%M:%S"

    first_visit_time = request.session.get('first_visit_time', None)
    if (first_visit_time is None):
        first_visit_time = datetime.now().strftime(date_time_format)
        request.session['first_visit_time'] = first_visit_time
    context = {
        'request_time': datetime.now().strftime(date_time_format),
        'first_visit_time': first_visit_time,
    }
    return render(request, 'index.html', context=context)

@method_decorator(login_required, name='get')
@method_decorator(login_required, name='post')
class MeasurementsView(TemplateView):

    template_name = 'measurements.html'
    form_class = MeasurementUploadForm
    initial = {'key': 'value'}

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.type_choices = [(d.id, d.name) for d in list(MeasurementDataType.objects.all())]
        self.source_choices = [(d.id, d.name) for d in list(Source.objects.all())]


    def get_context_data(self, **kwargs):   
        form = self.form_class(self.type_choices, self.source_choices, initial={
            'measurement_time': datetime.now(),
            'data_type': self.type_choices[0] if len(self.type_choices)> 0 else None,
            'source': self.source_choices[0] if len(self.source_choices)> 0 else None,
            'file': None
            })
        context = {
            'upload_form': form,
            'upload_status' : "please upload new data"
            }
        return context
 
    def post(self, request, *args, **kwargs):
        form = self.form_class(self.type_choices, self.source_choices, request.POST)
        if form.is_valid() and 'file' in request.FILES.keys():
            data_type : MeasurementDataType = MeasurementDataType.objects.filter(
                id__exact = request.POST['data_type']).first()
            source = Source.objects.filter(id__exact = request.POST['source']).first()
            test_json = CsvParser.to_json(request.FILES['file'])

            if not data_type.validate(test_json):
                upload_status = f"FAILURE: uploaded data is not valid for data type  '{data_type.name}'"
            else:
                measurement = Measurement()
                measurement.json_data = test_json
                measurement.data_type = data_type
                measurement.time_measured = request.POST['measurement_time']
                measurement.user_created = request.user
                measurement.user_changed = request.user
                measurement.source = source

                Measurement.save(measurement)

                upload_status = "SUCCES - saved content is " + test_json
                # return HttpResponseRedirect('/success/')
        else:
            upload_status = "FAILURE: Could not process the data"

        context = {
            'upload_form': form,
            'upload_status' : upload_status
            }

        return render(request, self.template_name, context)
