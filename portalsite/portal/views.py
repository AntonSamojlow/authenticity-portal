# standard
from datetime import datetime
from dataclasses import dataclass

# 3rd party
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import BaseListView, ListView

# local
from portal.forms import MeasurementUploadForm, MeasurementScoreForm
from portal.models import DATAHANDLER_CHOICES, DATAHANDLERS, Measurement, Model, Scoring, Source
from .core.data_handler import ValidationResult

def index(request: HttpRequest):

    date_time_format = "%d-%m-%Y, %H:%M:%S"

    first_visit_time = request.session.get('first_visit_time', None)
    if first_visit_time is None:
        first_visit_time = datetime.now().strftime(date_time_format)
        request.session['first_visit_time'] = first_visit_time
    context = {
        'request_time': datetime.now().strftime(date_time_format),
        'first_visit_time': first_visit_time,
    }
    return render(request, 'index.html', context=context)


class MeasurementsView(TemplateView, BaseListView):
    model = Measurement
    template_name = 'measurements.html'
    form_class = MeasurementUploadForm

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        # reload the choices
        self.source_choices = [(d.id, d.name) for d in list(Source.objects.all())]
        self.object_list = self.model.objects.all()

    def get_context_data(self, **kwargs):
        form = self.form_class(DATAHANDLER_CHOICES, self.source_choices, initial={
            'measured': datetime.now(),
            'data_handler': DATAHANDLER_CHOICES[0],
            'source': self.source_choices[0] if len(self.source_choices) > 0 else None,
            'file': None
        })
        context = BaseListView.get_context_data(self, **kwargs)
        context["upload_form"] = form
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(DATAHANDLER_CHOICES, self.source_choices, request.POST)
        name_already_exists: bool = Measurement.objects.filter(
            name__exact=request.POST['name']).count() > 0

        if not form.is_valid():
            return Result(False, "Data was not valid").render_view()

        if name_already_exists:
            return Result(False, "Name already exists",
                          "Please go back and choose a different name").render_view()

        if 'file' not in request.FILES.keys():
            return Result(False, "No file selected",
                          "Please go back and select a file to upload").render_view()

        data_handler = request.POST['data_handler']
        try:
            data = DATAHANDLERS[data_handler].load_from_file(request.FILES['file'])
        except UnicodeDecodeError as decode_error:
            return Result(False, "Unicode decoding error", details_formatted=str(decode_error)).render_view()
        except Exception as exc:
            return Result(False, "Unhandled - failed to read", details_formatted=str(exc)).render_view()
        source = Source.objects.filter(id__exact=request.POST['source']).first()

        measurement = Measurement()
        measurement.data = data
        measurement.data_handler = data_handler
        measurement.source = source
        measurement.name = request.POST['name']
        measurement.time_measured = request.POST['measured']
        measurement.user_created = request.user
        measurement.user_changed = request.user

        validation_results = measurement.validate()
        if sum([0 if result.success else 1 for result in validation_results]) > 0:
            return Result(False, "Validation failed",
                details_formatted = "\n".join([f"{result.name}: {result.details}" for result in validation_results])
            ).render_view()


        try:
            Measurement.save(measurement)
        except Exception as exc:
            # TODO: Replace this error by a generic one and write stacktrace only to log
            return Result(False, "Internal problem", str(exc)).render_view()

        return Result(True, "Data uploaded and saved",
                      link_address=measurement.get_absolute_url(),
                      link_text="See uploaded data").render_view()


class MeasurementDetailView(DetailView):
    model = Measurement
    template_name = 'measurement-detail.html'
    form_class = MeasurementScoreForm

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        # reload the choices
        self.model_choices = [(d.id, d.name) for d in list(Model.objects.all())]

    def get_context_data(self, **kwargs):
        context = DetailView.get_context_data(self, **kwargs)
        scores = Scoring.objects.filter(measurement__exact=self.get_object())
        context["scores"] = scores
        context["score_form"] = self.form_class(self.model_choices, initial={
            'model': self.model_choices[0] if len(self.model_choices) > 0 else None,
        })
        return context

    def post(self, request, *args, **kwargs):
        model: Model = Model.objects.filter(id__exact=request.POST['model']).first()
        scoring = model.score(self.get_object())
        print(scoring.value)
        print(scoring.measurement)
        print(scoring.model)
        try:
            Scoring.save(scoring)
        except Exception as exc:
            # TODO: Replace this error by a generic one and write stacktrace only to log
            return Result(False, "Internal problem", str(exc)).render_view()

        return Result(True, f"Computed score: {scoring.value}").render_view()


class ModelsView(ListView):
    model = Model
    template_name = 'models.html'

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.object_list = self.model.objects.all()

    def get_context_data(self, **kwargs):
        context = ListView.get_context_data(self, **kwargs)
        return context


class ModelDetailView(DetailView):
    model = Model
    template_name = 'model-detail.html'


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
            'result': 'Success' if self.success else 'Failure',
            'message': self.message,
            'details_formatted': self.details_formatted,
            'link_address': self.link_address,
            'link_text': self.link_text,
        }
        return render(request=None, template_name='result.html', context=context)
