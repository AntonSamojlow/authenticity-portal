# standard
from django.db import models
from django.urls import reverse
from django.conf import settings
from uuid import uuid4

# 3rd party
from numpy import ndarray

# local
from .core.data_handler import DataHandler, NumericCsvHandler, ValidationResult
from .core.model_type import LinearRegressionModel, ModelType, TestModelType

# initialize global types - note the keys are *limited in length* by virtue of the textfield they are used in
CHOICE_KEY_MAX_LENGTH = 10

DATAHANDLERS: dict[str, DataHandler] = {
    handler.lookup_id: handler for handler in [
        NumericCsvHandler()
    ]
}

MODELTYPES: dict[str, ModelType] = {
    model_type.lookup_id: model_type for model_type in
    [
        TestModelType(),
        LinearRegressionModel(2),
        LinearRegressionModel(5),
    ]
}

MODELTYPE_CHOICES = [(model_type.lookup_id,  model_type.name) for model_type in MODELTYPES.values()]
DATAHANDLER_CHOICES = [(handler.lookup_id,  handler.name) for handler in DATAHANDLERS.values()]


class Source(models.Model):
    """Source of a measurement"""

    name = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('source-detail', args=[str(self.id)])


class Measurement(models.Model):
    """Represents a measurement"""

    # base attributes
    name = models.CharField(
        unique=True,
        max_length=50)
    source = models.ForeignKey(Source, on_delete=models.RESTRICT)
    notes = models.TextField(
        help_text="description or notes for this measurement",
        null=True,
        blank=True)
    time_measured = models.DateTimeField(
        help_text="time the data was measured")

    # change tracking attributes
    time_created = models.DateTimeField(auto_now_add=True, help_text="fist time this measurement was saved to database")
    time_changed = models.DateTimeField(auto_now=True, help_text="last time this measurement was changed")
    user_created = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        help_text="user that created this measurement in the database",
        # exclude backwards relation from User to this field:
        related_name='+',
    )
    user_changed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        help_text="user that last changed this measurement in the database",
        # exclude backwards relation from User to this field:
        related_name='+',
    )

    # data interface
    data = models.TextField(help_text='file data, serialized to string in a suitable way')
    data_handler = models.CharField(max_length=CHOICE_KEY_MAX_LENGTH, choices=DATAHANDLER_CHOICES)

    @property
    def handler(self) -> DataHandler:
        return DATAHANDLERS[self.data_handler]

    class Meta:
        ordering = ['time_created']

    def __str__(self) -> str:
        return str(self.id)

    def get_absolute_url(self) -> str:
        """Returns the url to display the object."""
        return reverse('measurement-detail', args=[str(self.id)])

    # shortcuts via data handler
    def as_displaytext(self) -> str:
        return self.handler.to_displaytext(self.data)

    def as_json(self) -> str:
        return self.handler.to_json(self.data)

    def model_input(self) -> ndarray:
        return self.handler.to_model_input(self.data)

    def model_target(self) -> ndarray:
        return self.handler.to_model_target(self.data)

    def validate(self) -> list[ValidationResult]:
        return self.handler.validate(self.data)


class Model(models.Model):
    """Prediction model: combines with measurement to create a scoring"""

    name = models.CharField(unique=True, max_length=50)
    data = models.TextField(help_text='model data (weights, parameters, coefficients, etc.), serialized to string')

    # type interface
    model_type = models.CharField(max_length=CHOICE_KEY_MAX_LENGTH, choices=MODELTYPE_CHOICES)

    @property
    def get_type(self) -> ModelType:
        return MODELTYPES[self.model_type]

    def score(self, measurement: Measurement) -> 'Scoring':
        """Returns a new scoring"""
        scoring = Scoring()
        scoring.value = self.get_type.score(self, measurement)
        scoring.model = self
        scoring.measurement = measurement
        return scoring

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('model-detail', args=[str(self.id)])


class Scoring(models.Model):
    """Result of applying a model to a measurement"""

    value = models.FloatField(default=0)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('scoring-detail', args=[str(self.id)])
