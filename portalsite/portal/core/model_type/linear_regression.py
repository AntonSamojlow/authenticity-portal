# region imports
# standard
from json import dumps, loads
from typing import TYPE_CHECKING

# 3rd party
import numpy as np
from sklearn.linear_model import LinearRegression

# local
from .model_type import ModelStorageType, ModelType

# type hints
if TYPE_CHECKING:
    from portal.models import Model, Measurement

# endregion

class LinearRegressionModel(ModelType):
    """Base implementation of a linear regression model with a dfined nr of features."""

    def __init__(self, nr_features: int) -> None:
        super().__init__()
        # TODO: looks like we could remove the linear regression feature? The coef_ determine the model fully...
        self.nr_features = nr_features
        self.__id_ = f"LReg-{self.nr_features}"
        if len(self.__id_) > 10:
            raise Exception("LinearRegressionModel with {} features is not supported (lookup id too long")

    @property
    def id_(self) -> str:
        """Identifier used in internal dictionaries - maximal length 10"""
        return self.__id_

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
            raise KeyError(self.id_ + " failed to load model (data lacking required keys)")
        if json_data['object_type'] != self.id_ + "-model_data":
            raise ValueError(self.id_ + " failed to load model (model data has wrong object_type)")
        lr = LinearRegression()
        lr.coef_ = np.array(json_data['coef_'])
        lr.intercept_ = json_data['intercept_']
        return lr

    def __get_model_data(self, lr_model: LinearRegression) -> ModelStorageType:
        json_dict = {
            'object_type': self.id_ + "-model_data",
            'coef_': lr_model.coef_.tolist(),
            'intercept_': lr_model.intercept_
        }
        return dumps(json_dict)

    def score(self, model: 'Model', measurement: 'Measurement') -> float:
        """Returns the score of a measurement against a model"""
        # TODO: how do we disintguish labelled and unlabelled measurements? check if model_target == None?
        model : LinearRegression = self.__load_model(model)
        score = model.score(measurement.model_input(), measurement.model_target())
        return score

    def predict(self, model: 'Model', measurement: 'Measurement') -> np.ndarray:
        """Returns the prediction of a measurement against a model"""
        model : LinearRegression = self.__load_model(model)
        return model.predict(measurement.model_input())

    def train(self,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple[ModelStorageType, float]:
        """Trains a model, returning the new model with its score"""
        X_list = [m.model_input() for m in measurements]
        y_list = [m.model_target() for m in measurements]
        lr_current = self.__load_model(model)
        lr_fitted = lr_current.fit(X_list, y_list)
        score = lr_fitted.score(X_list, y_list)
        return (self.__get_model_data(lr_fitted), score)
