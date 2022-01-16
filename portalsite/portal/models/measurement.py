"""Data base model: Measurement"""

# region imports
# standard
from typing import TYPE_CHECKING
from django.db import models
from django.urls import reverse
from django.conf import settings

# 3rd party
from numpy import ndarray

# local
from portal.core import DATAHANDLERS
from .source import Source
from .group import Group

# type hints
if TYPE_CHECKING:
    from core.dataclasses import ValidationResult
    from core.data_handler import DataHandler

# endregion


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

    groups = models.ManyToManyField(Group)

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
    data_handler = models.CharField(max_length=DATAHANDLERS.id_length, choices=DATAHANDLERS.choices)

    @property
    def handler(self) -> 'DataHandler':
        return DATAHANDLERS.get(self.data_handler)

    @property
    def is_labelled(self) -> bool:
        return not self.model_target is None

    # this is a not very elegant short cut - the length parameter should really be controlled in the view
    @property
    def groups_as_short_text(self) -> str:
        return self.groups_as_text(42)

    class Meta:
        ordering = ['time_created']

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self) -> str:
        """Returns the url to display the object."""
        return reverse('measurement-detail', args=[str(self.id)])

    def groups_as_text(self, max_length: int = None) -> str:
        """Returns a comma separated string of group names, truncated if specified."""
        text = ", ".join([l.name for l in self.groups.all()])
        if max_length is not None and len(text) > max_length:
            text = text[: max(1, max_length-3)] + "..."
        return text

    # shortcuts via data handler
    def as_displaytext(self) -> str:
        return self.handler.to_displaytext(self.data)

    def as_json(self) -> str:
        return self.handler.to_json(self.data)

    def model_input(self) -> ndarray:
        return self.handler.to_model_input(self.data)

    def model_target(self) -> ndarray:
        return self.handler.to_model_target(self.data)

    def validate(self) -> list['ValidationResult']:
        return self.handler.validate(self.data)
