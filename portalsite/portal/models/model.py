"""Data base model: Model"""

# region imports
# standard
from typing import TYPE_CHECKING

# 3rd party
from django.db import models
from django.urls import reverse
from django.conf import settings

# local
from portal.core import MODELTYPES
from .scoring import Scoring
from .prediction import Prediction
from .group import Group

# type hints
if TYPE_CHECKING:
    from portal.core.model_type import ModelType
    from portal.models import Measurement
# endregion


class Model(models.Model):
    """Prediction model: combines with measurement to create a scoring"""

    name = models.CharField(unique=True, max_length=50)
    data = models.TextField(help_text='model data (weights, parameters, coefficients, etc.), serialized to string')

    groups = models.ManyToManyField(Group)
    
    ready_for_prediction = models.BooleanField(default=False, 
        help_text="whether this model is ready to be used for predictions")

    # type interface
    model_type = models.CharField(max_length=MODELTYPES.id_length, choices=MODELTYPES.choices)

    # change tracking attributes
    time_created = models.DateTimeField(auto_now_add=True, help_text="fist time this measurement was saved to database")
    time_changed = models.DateTimeField(auto_now=True, help_text="last time this measurement was changed")
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        help_text="user that created this model in the database",
        # exclude backwards relation from User to this field:
        related_name='+',
    )
    user_changed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        help_text="user that last changed this model in the database",
        # exclude backwards relation from User to this field:
        related_name='+',
    )

    @property
    def get_type(self) -> 'ModelType':
        return MODELTYPES.get(self.model_type)

    @property
    def details_text(self) -> str:
        """A formatted text describing the concrete data/paramters of the given model"""
        return self.get_type.details_text(self)

    # this is a not very elegant short cut - the length parameter should really be controlled in the view
    @property
    def groups_as_short_text(self) -> str:
        return self.groups_as_text(42)
    class Meta:
        ordering = ['time_created']

    def groups_as_text(self, max_length : int = None) -> str:
        """Returns a comma separated string of group names, truncated if specified."""
        text = ", ".join([l.name for l in  self.groups.all()])
        if max_length is not None and len(text) > max_length:
            text = text[: max(1,max_length-3)] + "..."
        return text

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
