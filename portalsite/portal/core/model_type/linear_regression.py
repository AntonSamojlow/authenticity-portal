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
    """Base implementation of a linear regression model. Model details/data define the supported feature count."""

    @property
    def id_(self) -> str:
        """Identifier"""
        return "LinearRegr"

    @property
    def name(self) -> str:
        """Returns a *short, concise* name"""
        return "Linear regression"

    @property
    def description(self) -> str:
        """Description of the type, its uses, and  possbily refering to external docs"""
        return self.__doc__

    def details(self, model: 'Model') -> str:
        """A formatted text describing the concrete data/paramters of the given model"""
        lreg = self.__load_model(model)
        return (
            f"Linear regressioin model for {len(lreg.coef_)} features.\n"
            +f"Coefficients={lreg.coef_}\n"
            +f"Intercept={lreg.intercept_}"
        )

    def __load_model(self, model: 'Model') -> LinearRegression:
        json_data: dict = loads(model.data)
        if ('object_type' not in json_data.keys()
            or 'coef_' not in json_data.keys()
            or 'intercept_' not in json_data.keys()):
            raise KeyError(self.id_ + " failed to load model (data lacking required keys)")
        if json_data['object_type'] != self.id_ + "-model_data":
            raise ValueError(self.id_ + " failed to load model (model data has wrong object_type)")
        lreg = LinearRegression()
        lreg.coef_ = np.array(json_data['coef_'])
        lreg.intercept_ = json_data['intercept_']
        return lreg

    def __get_model_data(self, lr_model: LinearRegression) -> ModelStorageType:
        json_dict = {
            'object_type': self.id_ + "-model_data",
            'coef_': lr_model.coef_.tolist(),
            'intercept_': lr_model.intercept_
        }
        return dumps(json_dict)

    def score(self, model: 'Model', measurement: 'Measurement') -> float:
        """Returns a models score, evaluated against a _labelled_ measurement (throws/undefined if unlabelled)"""
        model : LinearRegression = self.__load_model(model)
        score = model.score(measurement.model_input(), measurement.model_target())
        return score

    def predict(self, model: 'Model', measurement: 'Measurement') -> np.ndarray:
        """Returns a models prediction of a measurement"""
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
