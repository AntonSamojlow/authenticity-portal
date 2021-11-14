from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('measurements', views.measurements, name='measurements')
]
