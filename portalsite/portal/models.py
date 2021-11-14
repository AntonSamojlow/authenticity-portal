from django.db import models
from django.urls import reverse
from django.conf import settings


class MeasurementDataType(models.Model):
    """Measurement data type"""

    name = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('measurement-data-type', args=[str(self.id)])


class Source(models.Model):
    """Source of a measurement"""

    name = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('source', args=[str(self.id)])


class Measurement(models.Model):
    """Represents a measurement"""

    json_data = models.TextField(
        help_text='json object containing the measurement data')
    data_type = models.ForeignKey(MeasurementDataType, on_delete=models.RESTRICT)

    source = models.ForeignKey(Source, on_delete=models.RESTRICT)

    notes = models.TextField(
        help_text="description or notes for this measurement",
        null=True,
        blank=True)
    time_measured = models.DateTimeField(
        help_text="time the data was measured")

    # change tracking
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

    class Meta:
        ordering = ['time_created']

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('measurement', args=[str(self.id)])


class ModelType(models.Model):
    """Type of a prediction model"""

    name = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('model-type', args=[str(self.id)])


class Model(models.Model):
    """Prediction model: combines with measurement to create a scoring"""

    name = models.CharField(unique=True, max_length=50)
    type = models.ForeignKey(ModelType, on_delete=models.RESTRICT)
    data_type = models.ForeignKey(MeasurementDataType, on_delete=models.RESTRICT)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('model', args=[str(self.id)])


class Scoring(models.Model):
    """Result of applying a model to a measurement"""

    value = models.FloatField(default=0)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.id)
    
    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('scoring', args=[str(self.id)])
