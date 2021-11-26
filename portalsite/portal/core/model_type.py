
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..models import Model, Measurement

class ModelType(ABC):
    """Type of a prediction model"""

    @property
    @abstractmethod

    def name(self) -> str:
        """Returns a *short, concise* name"""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the type, its uses, and  possbily refering to external docs"""

    @abstractmethod
    def score(self, model: 'Model', measurement: 'Measurement') -> float:
        """Returns the score of a measurement against a model"""

    @classmethod
    @abstractmethod
    def train(self,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple['Model', float]:
        """Trains a model, returning the new model with its score"""
   
class TestModelType(ModelType):
    """This model type is a dummy implementation for development and testing::
         - scoring will always return 0
         - training will always return the same 'model' and 0 score
    """

    @property
    def name(self) -> str:
        """Returns a *short, concise* name"""
        return "TestModelType"

    @property
    def description(self) -> str:
        """Description of the type, its uses, and  possbily refering to external docs"""
        return self.__doc__

    def score(self, model: 'Model', measurement: 'Measurement') -> float:
        """Returns the score of a measurement against a model"""
        return 0.0

    def train(self,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple['Model', float]:
        """Trains a model, returning the new model with its score"""
        return (model, 0.0)