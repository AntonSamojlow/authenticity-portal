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
        """Returns the score of a measurement against a model"""

    @abstractmethod
    def predict(self, model: 'Model', measurement: 'Measurement') -> np.ndarray:
        """Returns the prediction of a measurement against a model"""

    @classmethod
    @abstractmethod
    def train(cls,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple[ModelStorageType, float]:
        """Trains a model, returning the new model data with its score"""
