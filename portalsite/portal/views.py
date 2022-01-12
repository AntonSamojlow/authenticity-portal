# region imports
# standard
from typing import TYPE_CHECKING, Any
from datetime import datetime
from dataclasses import dataclass
from django import forms
from io import StringIO

# 3rd party
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.http.response import FileResponse, HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import BaseListView
from wsgiref.util import FileWrapper

# local
from portal.forms import (MeasurementUploadForm, 
    FilterForm, 
    ModelTrainForm, 
    NewLinearRegssionModelForm, NewSimcaModelForm, 
    NewTestModelForm, 
    CopyModelForm,
    PredictionUploadForm)

from portal.models import Measurement, Model, Source, Prediction, Group
from portal.core import DATAHANDLERS, SIMCAMODEL, TESTMODELTYPE, LINEARREGRESSIONMODEL
from portal.core.data_handler import DataHandler
from portal.core.model_type.simca.simca import SimcaParameters, LimitType


# type hints
if TYPE_CHECKING:
    from django.db.models.query import QuerySet
# endregion


def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html', context={})

def info(request: HttpRequest) -> HttpResponse:
    return render(request, 'info.html', context={})

def measurementdownload(request: HttpRequest, pk: int) -> HttpResponse:
    measurement: Measurement = Measurement.objects.get(pk=pk)
    # measurement.data_handler
    handler: DataHandler = measurement.handler

    file = handler.to_file(measurement.data)

    response = HttpResponse(file, content_type='application/csv')
    response['Content-Length'] = file.tell()
    response['Content-Disposition'] = f'attachment; filename={measurement.name}.csv'

    return response

def _get_measurements_page(group_ids: list, 
    request: HttpRequest,
    compatible_model: Model = None):

    objects = Measurement.objects.none()
    if FilterForm.ALL in group_ids:
        objects = Measurement.objects.all()
    else:
        for group_id in group_ids:
            objects = objects | Measurement.objects.filter(groups__id=group_id) 

    if compatible_model is not None:
        compatible_objects = []
        for m in objects.distinct():
            if compatible_model.is_compatible(m):
                compatible_objects.append(m)
        return Paginator(compatible_objects, 10).get_page(request.GET.get('page'))
            
    return Paginator(objects.distinct(), 10).get_page(request.GET.get('page'))
     
def _get_models_page(group_ids: list, request: HttpRequest, only_ready_for_prediction: bool = False):
    objects = Model.objects.none()
    if FilterForm.ALL in group_ids:
        objects = Model.objects.all()
    else:
        for group_id in group_ids:
            objects = objects | Model.objects.filter(groups__id=group_id) 
    
    objects = objects.distinct()
    if only_ready_for_prediction:
        objects = objects.filter(ready_for_prediction=True)

    return Paginator(objects.distinct(), 10).get_page(request.GET.get('page'))
     
class MeasurementsView(TemplateView):
    model = Measurement
    template_name = 'measurements.html'

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.source_choices = list((d.id, d.name) for d in Source.objects.all())
        self.groups_chocies = list((l.id, l.name) for l in Group.objects.all())

    def get_context_data(self, **kwargs):
        form = MeasurementUploadForm(DATAHANDLERS.choices, self.source_choices, self.groups_chocies, initial={
            'measured': datetime.now(),
            'data_handler': DATAHANDLERS.choices[0],
            'source': self.source_choices[0] if len(self.source_choices) > 0 else None,
            'groups': self.groups_chocies[0] if len(self.groups_chocies) > 0 else None,
            'file': None
        })

        group_id = FilterForm.ALL
        if self.request.GET and 'group_filter' in self.request.GET:
            group_id = self.request.GET.get('group_filter')

        context= {
            'group_filter' : FilterForm
            (
                'group_filter',
                'group',
                list((l.id, l.name) for l in Group.objects.all()),
                initial=group_id,
                includeAll=True
            ),       
            'upload_form' : form,
            'measurements_page' : _get_measurements_page([group_id], self.request)
        }
        return context

    def post(self, request, *args, **kwargs):
        form = MeasurementUploadForm(DATAHANDLERS.choices, self.source_choices, self.groups_chocies, request.POST)
        name_already_exists: bool = Measurement.objects.filter(
            name__exact=request.POST['name']).count() > 0

        if not form.is_valid():
            return Result(False, "Data was not valid").render_view()

        form_data = form.cleaned_data

        if name_already_exists:
            return Result(False, "Name already exists",
                          "Please go back and choose a different name").render_view()

        if 'file' not in request.FILES.keys():
            return Result(False, "No file selected",
                          "Please go back and select a file to upload").render_view()

        data_handler = form_data['data_handler']
        try:
            data = DATAHANDLERS.get(data_handler).load_from_file(request.FILES['file'])
        except UnicodeDecodeError as decode_error:
            return Result(False, "Unicode decoding error", details_formatted=str(decode_error)).render_view()
        # except Exception as exc:
        #     return Result(False, "Unhandled - failed to read", details_formatted=str(exc)).render_view()
        source = Source.objects.filter(id__exact=form_data['source']).first()

        measurement = Measurement()
        measurement.data = data
        measurement.data_handler = data_handler
        measurement.source = source        
        measurement.name = form_data['name']
        measurement.time_measured = form_data['measured']
        measurement.user_created = request.user
        measurement.user_changed = request.user
        measurement.notes = form_data['notes']

        validation_results = measurement.validate()
        if sum([0 if result.success else 1 for result in validation_results]) > 0:
            return Result(False, "Validation failed", details_formatted="\n".join(
                [f"{result.name}: {result.details}" for result in validation_results])).render_view()

        try:
            Measurement.save(measurement)
            if 'groups' in  form_data:
                for group_id_string in form_data['groups']:
                    measurement.groups.add(int(group_id_string))
        except Exception as exc:
            # TODO: Replace this error by a generic one and write stacktrace only to log
            return Result(False, "Internal problem", str(exc)).render_view()

        return Result(True, "Data uploaded and saved",
                      link_address=measurement.get_absolute_url(),
                      link_text="See uploaded data").render_view()


class PredictView(TemplateView):
    template_name = 'predict.html'

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.source_choices = list((d.id, d.name) for d in Source.objects.all())
        self.groups_chocies = list((l.id, l.name) for l in Group.objects.all())

    def get_context_data(self, pk:int, **kwargs: any) -> dict[str, any]:
        context = TemplateView.get_context_data(self, **kwargs)

        model: Model = Model.objects.get(pk=pk)

        group_id = FilterForm.ALL
        if self.request.GET and 'group_filter' in self.request.GET:
            group_id = self.request.GET.get('group_filter')

        context['group_filter'] = FilterForm(
                'group_filter',
                'group',
                list((l.id, l.name) for l in Group.objects.all()),
                initial=group_id,
                includeAll=True)

        context['model'] = model
        context['upload_form'] = PredictionUploadForm(DATAHANDLERS.choices)
        context['measurements_page'] = _get_measurements_page([group_id], self.request, model)
        context['link_to_download'] = True
        return context
    
    def post(self, request: HttpRequest, *args, **kwargs):
        if 'pk' not in kwargs:
            return Result(False, "Internal error", details_formatted="argument 'pk' missing, model can not be identified").render_view()
        model : Model = Model.objects.get(pk=kwargs['pk'])

        form = PredictionUploadForm(DATAHANDLERS.choices,request.POST)
        if not form.is_valid():
            return Result(False, "Data was not valid").render_view()
        form_data = form.cleaned_data
    
        if 'file' not in request.FILES.keys():
            return Result(False, 
                        "No file selected",
                        "Please provide a file to upload").render_view()

        data_handler = form_data['data_handler']
        try:
            data = DATAHANDLERS.get(data_handler).load_from_file(request.FILES['file'])
        except UnicodeDecodeError as decode_error:
            return Result(False, "Unicode decoding error", details_formatted=str(decode_error)).render_view()
        # except Exception as exc:
        #     return Result(False, "Unhandled - failed to read", details_formatted=str(exc)).render_view()

        # store temporary measurement in database
        timenow = datetime.now()
        timestamp = timenow.strftime("%Y-/%m-/%d_%H:%M:%S.%f")

        measurement = Measurement()
        measurement.data = data
        measurement.data_handler = data_handler
        measurement.source = Source.objects.first()
        measurement.name = f"temp_{timestamp}" 
        measurement.time_measured = timenow
        measurement.user_created = request.user
        measurement.user_changed = request.user
        measurement.notes = f"temporary data upload for prediction with model '{model.name}' (id'{model.id}')"
        validation_results = measurement.validate()
        if sum([0 if result.success else 1 for result in validation_results]) > 0:
            return Result(False, "Validation failed", details_formatted="\n".join(
                [f"{result.name}: {result.details}" for result in validation_results])).render_view()

        Measurement.save(measurement)

        if not model.is_compatible(measurement):
            measurement.delete()
            return Result(False, "Data incompatible", details_formatted=str("The submitted measurement is not compatible with the model")).render_view()

        prediction : Prediction = model.predict(measurement)
        
        result_details_formatted = str(f"Predicted values are: {prediction.result}"
            + f"\nPrediction score is: {prediction.score}")
        try:
            measurement.delete()
        except Exception as exc:
            result_details_formatted += f"\nFailed to remove uploaded temporary files - please clean up manually ({exc})"

        return Result(True, "Prediction computed", 
            details_formatted=result_details_formatted).render_view()

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
        
        modeltype_by_modelid = {m.id : m.model_type for m in Model.objects.all()}

        context['model_filter'] = FilterForm(
            'model_filter',
            'model',
            list(set((p.model.id, f"{p.model.name} ({modeltype_by_modelid[p.model.id]})") for p in predictions)),
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

class ModelsView(TemplateView):
    template_name = 'models.html'

    def __init__(self, **kwargs: any) -> None:
        super().__init__(**kwargs)
        self.groups_choices = list((l.id, l.name) for l in Group.objects.all())


    def get_context_data(self, **kwargs):      
        group_id = FilterForm.ALL
        if self.request.GET and 'group_filter' in self.request.GET:
            group_id = self.request.GET.get('group_filter')

        lr_model = {
            'form' : NewLinearRegssionModelForm(self.groups_choices),
            'description' : LINEARREGRESSIONMODEL.description,
            'name' : "Linear Regression Model"
        }

        simca_model = {
            'form' : NewSimcaModelForm(SIMCAMODEL.LIMITTYPE_CHOICES, self.groups_choices),
            'description' : SIMCAMODEL.description,
            'name' : "SIMCA model"
        }

        context = {  
            'group_filter' : FilterForm
            (
                'group_filter',
                'group',
                list((l.id, l.name) for l in Group.objects.all()),
                initial=group_id,
                includeAll=True
            ),    
            'active_model' : lr_model,
            'other_models' : [simca_model],   
            'new_lreg_model_form' : NewLinearRegssionModelForm(self.groups_choices),
            # 'new_test_model_form' : NewTestModelForm(),
            'new_simca_model_form' : NewSimcaModelForm(SIMCAMODEL.LIMITTYPE_CHOICES, self.groups_choices),
            'models_page' : _get_models_page([group_id], self.request)
        } 
        return context

    def post(self, request : HttpRequest, *args, **kwargs):
        if 'new_lreg_model_submit' in request.POST:
            form = NewLinearRegssionModelForm(self.groups_choices, request.POST)
            model_type = LINEARREGRESSIONMODEL
        
        elif 'new_test_model_submit' in request.POST:
            form = NewTestModelForm(request.POST)
            model_type = TESTMODELTYPE
        
        elif 'new_simca_model_submit' in request.POST:
            form = NewSimcaModelForm(SIMCAMODEL.LIMITTYPE_CHOICES, self.groups_choices, request.POST)
            model_type = SIMCAMODEL

        if not form.is_valid():
            return Result(False, "Data was not valid").render_view()
        
        form_data = form.cleaned_data
        name = form_data.get('name')
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
        elif 'new_simca_model_submit' in request.POST:
            parameters = SimcaParameters(
                float(request.POST['alpha']),
                float(request.POST['gamma']),
                int(request.POST['components']),
                LimitType(int(request.POST['limit_type'])),
                bool('scale' in request.POST and request.POST['scale']),
            )
            model.data = SIMCAMODEL.default_data(int(request.POST['features']),
                parameters=parameters)

        model.save()

        if 'groups' in  form_data:
            for group_id_string in form_data['groups']:
                model.groups.add(int(group_id_string))

        return Result(True, f"New model '{name}' created",
                      link_address=model.get_absolute_url(),
                      link_text="Details of the new model").render_view()

class ModelDetailView(DetailView):
    model = Model
    template_name = 'model-detail.html'

    def get_context_data(self, **kwargs):
        group_id = FilterForm.ALL
        if self.request.GET and 'group_filter' in self.request.GET:
            group_id = self.request.GET.get('group_filter')
     
        context = DetailView.get_context_data(self, **kwargs)
       
        context['group_filter'] = FilterForm(
            'group_filter',
            'group',
            list((l.id, l.name) for l in Group.objects.all()),
            initial=group_id,
            includeAll=True)       
        context["train_form"] = ModelTrainForm(self._get_trainable_measurements(group_id))
        context["copy_form"] = CopyModelForm()
        return context

    def _get_trainable_measurements(self, group_id : str = FilterForm.ALL) -> 'QuerySet':
        # TODO This is ahighly ineffecient way to gather all trainable measurements:
        # 1. we walk through  Measurements twice: first retireving them, then just for generating a Queryset object
        # - possible quick fix: use a MultipleChoiceField instaed and handle list of choices manually
        # 2. the need to retrieve all measurements from db to check compatible is an even bigger design issue
        # - need a stricter/better/more efficient way to figure out compatability just absed on a db fields (one query)
        model: Model = self.get_object()
        trainable_ids = []
        if group_id == FilterForm.ALL:
            filtered_measurements =  Measurement.objects.all()
        else:
            filtered_measurements = Measurement.objects.filter(groups__id=group_id)

        for m in filtered_measurements:
            if m.is_labelled and model.is_compatible(m):
                trainable_ids.append(m.id)

        return Measurement.objects.filter(pk__in=trainable_ids)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if 'copy_submit' in request.POST:
            return self._post_copy(request)
        if 'train_submit' in request.POST:
            return self._post_train(request)
        if 'change_ready_flag' in request.POST:
            return self._post_change_ready_flag(request)
        
   

    def _post_copy(self, request: HttpRequest) -> HttpResponse:
        #validate        
        form = CopyModelForm(request.POST)
        if not form.is_valid():
            return Result(False, "Data was not valid").render_view()
        data = form.cleaned_data
        new_name = data.get('new_name')
        if Model.objects.filter(name__exact=new_name).count() > 0:
            return Result(False, "Name already exists",
                        "Please go back and choose a different name").render_view()
        
        # copy
        model: Model = self.get_object()
        new_model = Model()
        new_model.name = new_name
        new_model.user_created = request.user
        new_model.user_changed = request.user
        new_model.model_type = model.model_type
        new_model.data = model.data
        new_model.save()

        if 'new_lreg_model_submit' in request.POST:    
            model.data = LINEARREGRESSIONMODEL.default_data(int(request.POST['features']))
        elif 'new_test_model_submit' in request.POST:
            model.data = TESTMODELTYPE.default_data()
        model.save() 
        return Result(True, f"Copy '{new_name}' created",
                      link_address=new_model.get_absolute_url(),
                      link_text="Details of the copy").render_view()
    
    def _post_train(self, request: HttpRequest) -> HttpResponse:
        form = ModelTrainForm(self._get_trainable_measurements(), request.POST)
        if(form.is_valid()):
            data = form.cleaned_data
            name = data.get('name')

            print(request.user)
            print(request.user.get_all_permissions())
            if name.isspace(): name = None 

            if name and not request.user.has_perm('portal.add_model'):
                return Result(False, "Not allowed", "You do not have the rights to create new models").render_view()
            
            if not name and not request.user.has_perm('portal.change_model'):
                return Result(False, "Not allowed", "You do not have the rights to change existing models").render_view()

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
                raise exc
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

    def _post_change_ready_flag(self, request: HttpRequest) -> HttpResponse:
        model: Model = self.get_object()
        model.ready_for_prediction = not model.ready_for_prediction
        model.save() 
        return Result(True, f"Ready for prediction status changed to '{model.ready_for_prediction}'",
                      link_address=model.get_absolute_url(),
                      link_text="See model details").render_view()

class TopicView(TemplateView):
    template_name = 'topic.html'

    def get_context_data(self, topic, **kwargs: any) -> dict[str, any]:
        context = TemplateView.get_context_data(self, **kwargs)
        context['title'] = str.upper(topic[0]) + topic[1:]
        match topic:
            case 'iris':
                group_ids = list(g.id for g in Group.objects.filter(name__icontains='iris'))
                context['description_template'] = "topics/iris_description.html"
                context['measurements_page'] = _get_measurements_page(group_ids, self.request)
                context['models_page'] = _get_models_page(group_ids, self.request, True)

            case 'salmon':
                group_ids = list(g.id for g in Group.objects.filter(name__icontains='salmon'))
                context['description_template'] = "topics/generic_description.html"
                context['measurements_page'] = _get_measurements_page(group_ids, self.request)
                context['models_page'] = _get_models_page(group_ids, self.request, True)

            case 'vanilla':
                group_ids = list(g.id for g in Group.objects.filter(name__icontains='vanilla'))
                context['description_template'] = "topics/generic_description.html"
                context['measurements_page'] = _get_measurements_page(group_ids, self.request)
                context['models_page'] = _get_models_page(group_ids, self.request, True)

            case _:
                context['description_template'] = "topics/generic_description.html"
                context['measurements_page'] = None
                context['models_page'] = None

        return context


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
