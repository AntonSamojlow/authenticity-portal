from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('measurements', views.MeasurementsView.as_view(), name='measurements'),
    path('measurement/<int:pk>', views.MeasurementDetailView.as_view(), name='measurement')
]
