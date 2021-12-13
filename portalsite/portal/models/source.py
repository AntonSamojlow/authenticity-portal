"""Data base model: Source"""

# region imports
# standard
from django.db import models
from django.urls import reverse

# 3rd party

# local

# type hints

# endregion


class Source(models.Model):
    """Source of a measurement"""

    name = models.CharField(unique=True, max_length=50)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        """Returns the url to display the object."""
        return reverse('source-detail', args=[str(self.id)])
