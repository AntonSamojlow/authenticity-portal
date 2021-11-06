from django.db import models

# Create your models here.


class MeasurementData(models.Model):
    """Data of some measurement"""

    JSONData = models.TextField(
        help_text='json object describing the measurement')


def __str__(self):
    return self.id


def get_aboslute_url(self):
    return reverse('measurement-data', aref=[str(self.id)])
