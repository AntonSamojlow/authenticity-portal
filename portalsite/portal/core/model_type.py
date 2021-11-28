from json import dumps, loads
from abc import ABC, abstractmethod
from sklearn.linear_model import LinearRegression

from typing import TYPE_CHECKING, TypeAlias

import numpy as np

if TYPE_CHECKING:
    from ..models import Model, Measurement


ModelStorageType: TypeAlias = str
"""Format/type used to store the model data in the database."""


class ModelType(ABC):
    """Type of a prediction model"""

    @property
    @abstractmethod
    def lookup_id(self) -> str:
        """Identifier used in internal dictionaries - maximal length 10"""

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
              max_seconds: int) -> tuple[ModelStorageType, float]:
        """Trains a model, returning the new model data with its score"""


class TestModelType(ModelType):
    """This model type is a dummy implementation for development and testing::
         - scoring will always return 0
         - training will always return the same 'model' and 0 score
    """

    @property
    def lookup_id(self) -> str:
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

    def train(self,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple[ModelStorageType, float]:
        """Trains a model, returning the same model data with a score of 0"""
        return (model.data, 0.0)


class LinearRegressionModel(ModelType):
    """Base implementation of a linear regression model with a dfined nr of features."""

    def __init__(self, nr_features: int) -> None:
        super().__init__()
        # TODO: looks like we could remove the linear regression feature? The coef_ determine the model fully...
        self.nr_features = nr_features
        self.__lookup_id = f"LReg-{self.nr_features}"
        if len(self.__lookup_id) > 10:
            raise Exception("LinearRegressionModel with {} features is not supported (lookup id too long")

    @property
    def lookup_id(self) -> str:
        """Identifier used in internal dictionaries - maximal length 10"""
        return self.__lookup_id

    @property
    def name(self) -> str:
        """Returns a *short, concise* name"""
        return f"{self.nr_features}-feature linear regression"

    @property
    def description(self) -> str:
        """Description of the type, its uses, and  possbily refering to external docs"""
        return self.__doc__

    def __load_model(self, model: 'Model') -> LinearRegression:
        json_data: dict = loads(model.data)
        if ('object_type' not in json_data.keys()
            or 'coef_' not in json_data.keys()
            or 'intercept_' not in json_data.keys()):
            raise KeyError(self.lookup_id + " failed to load model (data lacking required keys)")
        if json_data['object_type'] != self.lookup_id + "-model_data":
            raise ValueError(self.lookup_id + " failed to load model (model data has wrong object_type)")
        lr = LinearRegression()
        lr.coef_ = np.array(json_data['coef_'])
        lr.intercept_ = json_data['intercept_']
        return lr

    def __get_model_data(self, lr_model: LinearRegression) -> ModelStorageType:
        json_dict = {
            'object_type': self.lookup_id + "-model_data",
            'coef_': lr_model.coef_.tolist(),
            'intercept_': lr_model.intercept_
        }
        return dumps(json_dict)

    def score(self, model: 'Model', measurement: 'Measurement') -> float:
        """Returns the score of a measurement against a model"""
        X = measurement.model_input()
        y = measurement.model_target()
        # TODO: how do we disintguish labelled and unlabelled measurements? check if y == None?
        model = self.__load_model(model)
        print(X)
        print(y)
        score = model.score(X, y)
        return score

    def train(self,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple['Model', float]:
        """Trains a model, returning the new model with its score"""
        X_list = [m.model_input() for m in measurements]
        y_list = [m.model_target() for m in measurements]
        lr_current = self.__load_model(model)
        lr_fitted = lr_current.fit(X_list, y_list)
        score = lr_fitted.score(X_list, y_list)
        return (self.__get_model_data(lr_fitted), score)
