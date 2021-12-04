"""Data base model: Scoring"""

# region imports
# standard
from django.db import models
from django.urls import reverse

# 3rd party

# local

# type hints

# endregion


class Scoring(models.Model):
    """Result of applying a model to a measurement"""

    value = models.FloatField(default=0)
    model = models.ForeignKey('Model', on_delete=models.CASCADE)
    measurement = models.ForeignKey('Measurement', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('scoring-detail', args=[str(self.id)])
