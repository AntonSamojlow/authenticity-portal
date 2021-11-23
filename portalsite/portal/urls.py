from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('measurements', login_required(views.MeasurementsView.as_view()), name='measurements'),
    path('measurement/<int:pk>', login_required(views.MeasurementDetailView.as_view()), name='measurement'),
    path('result', login_required(views.MeasurementDetailView.as_view()), name='result')
]
