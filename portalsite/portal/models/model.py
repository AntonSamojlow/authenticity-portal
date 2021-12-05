"""Data base model: Model"""

# region imports
# standard
from typing import TYPE_CHECKING

# 3rd party
from django.db import models
from django.urls import reverse

# local
from portal.core import MODELTYPES
from .scoring import Scoring
from .prediction import Prediction

# type hints
if TYPE_CHECKING:
    from portal.core.model_type import ModelType
    from portal.models import Measurement
# endregion


class Model(models.Model):
    """Prediction model: combines with measurement to create a scoring"""

    name = models.CharField(unique=True, max_length=50)
    data = models.TextField(help_text='model data (weights, parameters, coefficients, etc.), serialized to string')

    # type interface
    model_type = models.CharField(max_length=MODELTYPES.id_length, choices=MODELTYPES.choices)

    @property
    def get_type(self) -> 'ModelType':
        return MODELTYPES.get(self.model_type)

    @property
    def details_text(self) -> str:
        """A formatted text describing the concrete data/paramters of the given model"""
        return self.get_type.details_text(self)

    def score(self, measurement: 'Measurement') -> Scoring:
        """Returns a new scoring"""
        if not measurement.is_labelled:
            raise NotImplementedError("Can not score unlabelled measurements")
        return Scoring(
            value = self.get_type.score(self, measurement),
            model = self,
            measurement = measurement)

    def predict(self, measurement: 'Measurement') -> Prediction:
        """Returns a new prediction"""
        return Prediction(
            result = self.get_type.predict(self, measurement),
            score = self.get_type.score(self, measurement) if measurement.is_labelled else float('NaN'),
            model = self,
            measurement = measurement)

    def is_compatible(self, measurement: 'Measurement') -> bool:
        """Returns true iff the measurement is a valid input (for this models prediction)"""
        return self.get_type.compatible(self, measurement)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('model-detail', args=[str(self.id)])
