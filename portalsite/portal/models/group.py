"""Data base model: Group"""

# region imports
# standard
from django.db import models
from django.urls import reverse

# 3rd party

# local

# type hints

# endregion


class Group(models.Model):
    """Group, used to classify objects. Holds a descriptive text."""

    name = models.CharField(unique=True, max_length=20)
    description = models.TextField()

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('group-detail', args=[str(self.id)])

