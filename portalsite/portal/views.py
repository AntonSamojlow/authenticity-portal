from datetime import datetime
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import BaseListView
from dataclasses import dataclass

from portal.forms import MeasurementUploadForm
from portal.models import MeasurementDataType, Measurement, Source
from .dataimport.csvparser import CsvParser


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

class MeasurementsView(TemplateView, BaseListView):
    template_name = 'measurements.html'
    form_class = MeasurementUploadForm
    initial = {'key': 'value'}
    model = Measurement

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        # reload the choices
        self.type_choices = [(d.id, d.name) for d in list(MeasurementDataType.objects.all())]
        self.source_choices = [(d.id, d.name) for d in list(Source.objects.all())]
        self.object_list = Measurement.objects.all()

    def get_context_data(self, **kwargs):
        form = self.form_class(self.type_choices, self.source_choices, initial={
            'measured': datetime.now(),
            'data_type': self.type_choices[0] if len(self.type_choices) > 0 else None,
            'source': self.source_choices[0] if len(self.source_choices) > 0 else None,
            'file': None
        })
        context = BaseListView.get_context_data(self, **kwargs)
        context["upload_form"] = form
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.type_choices, self.source_choices, request.POST)
        name_already_exists : bool =  Measurement.objects.filter(
           name__exact=request.POST['name']).count() > 0



        if not form.is_valid():
            return Result(False, "Data was not valid").render_view()

        if name_already_exists:
            return Result(False, "Name already exists",
            "Please go back and choose a different name").render_view()

        if 'file' not  in request.FILES.keys():
            return Result(False, "No file selected",
            "Please go back and select a file to upload").render_view()

        data_type = MeasurementDataType.objects.filter(id__exact=request.POST['data_type']).first()
        source = Source.objects.filter(id__exact=request.POST['source']).first()
        test_json = CsvParser.to_json(request.FILES['file'])

        measurement = Measurement()
        measurement.name =  request.POST['name']
        measurement.json_data = test_json
        measurement.data_type = data_type
        measurement.time_measured = request.POST['measured']
        measurement.user_created = request.user
        measurement.user_changed = request.user
        measurement.source = source

        try:
            Measurement.save(measurement)
        except Exception as exc:
            ### TODO: Replace this error by a generic one and write stacktrace only to log
            return Result(False, "Internal problem", str(exc)).render_view()

        return Result(True, "Data uploaded and saved", 
         link_address= measurement.get_absolute_url(),
         link_text= "See uploaded data").render_view()

class MeasurementDetailView(DetailView):
    model = Measurement
    template_name = 'measurement.html'



@dataclass
class Result():
    """Result of an operation"""
    success: bool
    message: str
    details_formatted: str = None
    link_address: str = None
    link_text: str = None

    def render_view(self) -> HttpResponse:
        context = {
            'result' : 'Success' if self.success else 'Failure',
            'message' : self.message,
            'details_formatted' : self.details_formatted,
            'link_address' : self.link_address,
            'link_text' : self.link_text,
        }
        return render(request=None, template_name='result.html', context=context)
