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


class Scoring(models.Model):
    """Performance evaluation of a models prediction against a labelled measurement"""

    value = models.FloatField(default=0)
    model = models.ForeignKey('Model', on_delete=models.CASCADE)
    measurement = models.ForeignKey('Measurement', on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True, help_text="time it was generated")

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('scoring-detail', args=[str(self.id)])
