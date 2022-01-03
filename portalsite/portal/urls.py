from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('models', login_required(views.ModelsView.as_view()), name='models'),
    path('models/<int:pk>', login_required(views.ModelDetailView.as_view()), name='model-detail'),
    path('measurements', login_required(views.MeasurementsView.as_view()), name='measurements'),
    path('measurement/<int:pk>', login_required(views.MeasurementDetailView.as_view()), name='measurement-detail'),
    path('result', login_required(views.MeasurementDetailView.as_view()), name='result'),
    path('topic/<topic>', login_required(views.TopicView.as_view()), name='topic')
]
