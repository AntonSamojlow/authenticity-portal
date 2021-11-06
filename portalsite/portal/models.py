from django.db import models
from django.urls import reverse
# Create your models here.


class MeasurementData(models.Model):
    """Data of some measurement"""

    JSONData = models.TextField(
        help_text='json object describing the measurement')


def __str__(self):
    return self.id
