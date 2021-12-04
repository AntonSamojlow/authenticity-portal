# region imports
# standard
from typing import TYPE_CHECKING

# 3rd party
import numpy as np

# local
from .model_type import ModelStorageType, ModelType

# type hints
if TYPE_CHECKING:
    from portal.models import Model, Measurement

# endregion

class TestModelType(ModelType):
    """This model type is a dummy implementation for development and testing::
         - scoring will always return 0
         - training will always return the same 'model' and 0 score
    """

    @property
    def id_(self) -> str:
        """Identifier used in internal dictionaries - maximal length 10"""
        return "Test"

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

    def predict(self, model: 'Model', measurement: 'Measurement') -> np.ndarray:
        """Returns the prediction of a measurement against a model"""
        return np.array(0.0)

    def train(self,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple[ModelStorageType, float]:
        """Trains a model, returning the same model data with a score of 0"""
        return (model.data, 0.0)
