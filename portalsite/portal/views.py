# region imports
# standard
from typing import TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass


# 3rd party
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import BaseListView

# local
from portal.forms import MeasurementUploadForm, FilterForm, ModelTrainForm, NewLinearRegssionModelForm, NewTestModelForm
from portal.models import Measurement, Model, Source, Prediction
from portal.core import DATAHANDLERS, TESTMODELTYPE, LINEARREGRESSIONMODEL

# type hints
if TYPE_CHECKING:
    from django.db.models.query import QuerySet
# endregion


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

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        # reload the choices
        self.source_choices = [(d.id, d.name) for d in list(Source.objects.all())]
        self.object_list = self.model.objects.all()

    def get_context_data(self, **kwargs):
        form = MeasurementUploadForm(DATAHANDLERS.choices, self.source_choices, initial={
            'measured': datetime.now(),
            'data_handler': DATAHANDLERS.choices[0],
            'source': self.source_choices[0] if len(self.source_choices) > 0 else None,
            'file': None
        })
        context = BaseListView.get_context_data(self, **kwargs)
        context["upload_form"] = form
        return context

    def post(self, request, *args, **kwargs):
        form = MeasurementUploadForm(DATAHANDLERS.choices, self.source_choices, request.POST)
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
            data = DATAHANDLERS.get(data_handler).load_from_file(request.FILES['file'])
        except UnicodeDecodeError as decode_error:
            return Result(False, "Unicode decoding error", details_formatted=str(decode_error)).render_view()
        # except Exception as exc:
        #     return Result(False, "Unhandled - failed to read", details_formatted=str(exc)).render_view()
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
            return Result(False, "Validation failed", details_formatted="\n".join(
                [f"{result.name}: {result.details}" for result in validation_results])).render_view()

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

    def _get_predict_choices(self) -> list[tuple[str, str]]:
        measurement: Measurement = self.get_object()
        choices = []
        for m in Model.objects.all():
            if m.is_compatible(measurement):
                choices.append((m.id, m.name))
        return choices

    def get_context_data(self, **kwargs):
        context = DetailView.get_context_data(self, **kwargs)

        model_id = FilterForm.ALL
        if self.request.GET and 'model_filter' in self.request.GET:
            model_id = self.request.GET.get('model_filter')
        predictions: list[Prediction] = list(Prediction.objects.filter(measurement__exact=self.get_object()))    

        filtered_predictions = []
        if model_id == FilterForm.ALL:
           filtered_predictions = predictions
        else:
            for p in predictions:
                if p.model.id == int(model_id):
                    filtered_predictions.append(p)
        
        context['model_filter'] = FilterForm(
            'model_filter',
            'model',
            list(set((p.model.id, p.model.name)for p in predictions)),
            initial=model_id,
            includeAll=True)       
        context['predictions_page'] = Paginator(filtered_predictions, 10).get_page(self.request.GET.get('page'))
        context['predict_filter'] = FilterForm('predict_filter', 'model', self._get_predict_choices())
        return context

    def post(self, request, *args, **kwargs):
        model: Model = Model.objects.filter(id__exact=request.POST['predict_filter']).first()
        prediction = model.predict(self.get_object())
        try:
            Prediction.save(prediction)
        except Exception as exc:
            # TODO: Replace this error by a generic one and write stacktrace only to log
            return Result(False, "Internal problem", str(exc)).render_view()

        return Result(
            True,
            "Computed prediction",
            f"Result:{prediction.result}\nScore:{prediction.score}"
        ).render_view()


class ModelsView(TemplateView, BaseListView):
    model = Model
    template_name = 'models.html'

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.object_list = self.model.objects.all()


    def get_context_data(self, **kwargs):        
        context = BaseListView.get_context_data(self, **kwargs)
        context['new_lreg_model_form'] = NewLinearRegssionModelForm()
        context['new_test_model_form'] = NewTestModelForm()
        return context

    def post(self, request : HttpRequest, *args, **kwargs):

        if 'new_lreg_model_submit' in request.POST:
            form = NewLinearRegssionModelForm(request.POST)
            model_type = LINEARREGRESSIONMODEL
        
        elif 'new_test_model_submit' in request.POST:
            form = NewTestModelForm(request.POST)
            model_type = TESTMODELTYPE

        if not form.is_valid():
            return Result(False, "Data was not valid").render_view()
        
        name: str = request.POST['name']
        if Model.objects.filter(name__exact=name).count() > 0:
            return Result(False, "Name already exists",
                        "Please go back and choose a different name").render_view()

        model = Model()
        model.name = name
        model.user_created = request.user
        model.user_changed = request.user
        model.model_type = model_type.id_

        if 'new_lreg_model_submit' in request.POST:    
            model.data = LINEARREGRESSIONMODEL.default_data(int(request.POST['features']))
        elif 'new_test_model_submit' in request.POST:
            model.data = TESTMODELTYPE.default_data()
        model.save()
        return Result(True, f"New model '{name}' created",
                      link_address=model.get_absolute_url(),
                      link_text="See model details").render_view()

class ModelDetailView(DetailView):
    model = Model
    template_name = 'model-detail.html'

    def get_context_data(self, **kwargs):
        context = DetailView.get_context_data(self, **kwargs)
        context["train_form"] = ModelTrainForm(self._get_trainable_measurements())
        return context

    def _get_trainable_measurements(self) -> 'QuerySet':
        # TODO This is ahighly ineffecient way to gather all trainable measurements:
        # 1. we walk through  Measurements twice: first retireving them, then just for generating a Queryset object
        # - possible quick fix: use a MultipleChoiceField instaed and handle list of choices manually
        # 2. the need to retrieve all measurements from db to check compatible is an even bigger design issue
        # - need a stricter/better/more efficient way to figure out compatability just absed on a db fields (one query)
        model: Model = self.get_object()
        trainable_ids = []
        for m in Measurement.objects.all():
            if m.is_labelled and model.is_compatible(m):
                trainable_ids.append(m.id)

        return Measurement.objects.filter(pk__in=trainable_ids)

    def post(self, request, *args, **kwargs):
        form = ModelTrainForm(self._get_trainable_measurements(), request.POST)
        if(form.is_valid()):
            data = form.cleaned_data
            name = data.get('name')
            if name and Model.objects.filter(name=name).count() > 0:
                return Result(False, "Model already exists", "Please choose a different name").render_view()

            measurements = list(data.get('measurements'))
            model: Model = self.get_object()
            old_score = sum([model.score(m).value for m in measurements])/len(measurements)
            try:
                trained_model_data, new_score = model.get_type.train(
                    model,
                    measurements,
                    max_iterations=1,
                    max_seconds=10)
            except Exception as exc:
                return Result(False, "Training failed", str(exc)).render_view()

            operation_text = ""
            if name:
                Model(name=name,
                      data=trained_model_data,
                      user_created=request.user,
                      user_changed=request.user,
                      model_type=model.model_type).save()
                operation_text = f"'{name}' was saved"
            else:
                model.data = trained_model_data
                model.user_changed = request.user
                model.save()
                operation_text = f"'{model.name}' was updated"

            return Result(True, "Training finished",
                          f"score before: {old_score}\nscore after: {new_score}\n{operation_text}").render_view()


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
