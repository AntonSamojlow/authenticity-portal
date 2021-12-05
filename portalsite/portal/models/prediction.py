"""Data base model: Scoring"""

# region imports
# standard
from typing import TYPE_CHECKING
from django.db import models
from django.urls import reverse

# 3rd party

# local

# type hints
if TYPE_CHECKING:
    from .measurement import Measurement
    from .model import Model

# endregion


class Prediction(models.Model):
    """Result of applying a model to a measurement"""

    score = models.FloatField(null=True, blank= True)
    result = models.TextField()
    model = models.ForeignKey('Model', on_delete=models.CASCADE)
    measurement = models.ForeignKey('Measurement', on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True, help_text="time it was generated")

   
    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('prediction-detail', args=[str(self.id)])
