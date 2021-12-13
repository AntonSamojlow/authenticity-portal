# region imports
# standard
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING, TypeAlias
# 3rd party
import numpy as np

# local
from portal.core.named_id_manager import NamedIdObject

# type hints
if TYPE_CHECKING:
    from portal.models import Model, Measurement

# endregion

ModelStorageType: TypeAlias = str
"""Format/type used to store the model data in the database."""

class ModelType(ABC,NamedIdObject):
    """Type of a prediction model"""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the type, its uses, and  possbily refering to external docs"""

    @abstractmethod
    def score(self, model: 'Model', measurement: 'Measurement') -> float:
        """Returns a models score, evaluated against a _labelled_ measurement (throws/undefined if unlabelled)"""

    @abstractmethod
    def predict(self, model: 'Model', measurement: 'Measurement') -> np.ndarray:
        """Returns a models prediction of a measurement"""

    @abstractmethod
    def details_text(self, model: 'Model') -> str:
        """A formatted text describing the concrete data/paramters of the given model"""

    @abstractmethod
    def compatible(self, model: 'Model', measurement: 'Measurement') -> bool:
        """Returns true iff the measurement is a valid (prediction) input for the model"""

    @classmethod
    @abstractmethod
    def train(cls,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple[ModelStorageType, float]:
        """Trains a model, returning the new model data with its score"""
