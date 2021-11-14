from datetime import datetime
from django.core.files.uploadedfile import UploadedFile
from django.http.request import HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from portal.forms import MeasurementUploadForm
from portal.models import MeasurementDataType, Measurement, Source

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

@login_required
def measurements(request: HttpRequest):
    uploaded_content = "please upload new data"
    type_choices = [(d.id, d.name) for d in list(MeasurementDataType.objects.all())]
    source_choices = [(d.id, d.name) for d in list(Source.objects.all())]

    def handle_uploaded_file(file: UploadedFile) -> str:
        read_text = ""
        for chunk in file.chunks():
            read_text += str(chunk)
        return read_text

    # If this is a POST request then process the Form data
    if request.method == 'POST':
        form = MeasurementUploadForm(type_choices, source_choices, request.POST)
        if form.is_valid() and 'file' in request.FILES.keys():
            print(request.POST['data_type'])
            data_type = MeasurementDataType.objects.filter(id__exact = request.POST['data_type']).first()
            source = Source.objects.filter(id__exact = request.POST['source']).first()
            file_content = handle_uploaded_file(request.FILES['file'])

            measurement = Measurement()
            measurement.json_data = file_content
            measurement.data_type = data_type
            measurement.time_measured = request.POST['measurement_time']
            measurement.user_created = request.user
            measurement.user_changed = request.user
            measurement.source = source
            Measurement.save(measurement)

            uploaded_content = "SUCCES - saved content is " + file_content
        else:
            uploaded_content = "FAILED TO PROCESS!"

    # If this is a GET (or any other method) create the default form.
    else:
        measurement_time = datetime.now()
        form = MeasurementUploadForm(type_choices, source_choices, initial={
            'measurement_time': measurement_time,
            'data_type': type_choices[0] if len(type_choices)> 0 else None,
            'source': source_choices[0] if len(source_choices)> 0 else None,
            'file': None
            })

    context = {
        'upload_form': form,
        'uploaded_content' : uploaded_content
    }
    return render(request, 'measurements.html', context=context)
