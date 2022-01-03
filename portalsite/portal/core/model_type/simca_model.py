# region imports
# standard
from json import dumps, loads
from types import new_class
from typing import TYPE_CHECKING

# 3rd party
import numpy as np


# local
from .model_type import ModelStorageType, ModelType
from .simca.simca import Simca, SimcaParameters, LimitType
from .simca.serializer import SimcaSerializer

# type hints
if TYPE_CHECKING:
    from portal.models import Model, Measurement

# endregion

class SimcaModel(ModelType):
    """
    Base implementation of a simca model: Soft Independent Modelling of Class Analogy.

    Further info:
        - https://mdatools.com/docs/simca.html
        - https://doi.org/10.1002/cem.2506
    """

    __instance_id = "Simca"

    LIMITTYPE_CHOICES = [(limit.value , limit.name) for limit in LimitType]

    @property
    def id_(self) -> str:
        """Identifier used in internal dictionaries - maximal length 10"""
        # all instances of this type are the same
        return self.__instance_id

    @property
    def name(self) -> str:
        """Returns a *short, concise* name"""
        return "SimcaModel"

    @property
    def description(self) -> str:
        """Description of the type, its uses, and  possbily refering to external docs"""
        return self.__doc__

    def details_text(self, model: 'Model') -> str:
        """A formatted text describing the concrete data/paramters of the given model"""
        simca = self.__load_model(model)
        return (
            f"Simca model for numerical data with {int(simca.data.shape[1])} features\n"
            +"Model parameters:\n"
            +f"- alpha: {simca.parameters.alpha}\n"
            +f"- gamma: {simca.parameters.gamma}\n"
            +f"- limit type: {simca.parameters.limit_type}\n"
            +f"- components: {simca.parameters.n_comp}\n"
            +f"- scale: {simca.parameters.scale}"
        )

    def compatible(self, model: 'Model', measurement: 'Measurement') -> bool:
        """Returns true iff the measurement is a valid (prediction) input for the model"""
        features = int(self.__load_model(model).data.shape[1])
        shape : tuple = measurement.model_input().shape
        if len(shape) != 2:
            return False
        if int(shape[1]) != features:
            return False
        return True

    def __load_model(self, model: 'Model') -> Simca:
        json_data: dict = loads(model.data)
        return SimcaSerializer().from_dict(json_data)
    
    def __get_model_data(self, simca: Simca) -> ModelStorageType:
        return dumps(SimcaSerializer().to_dict(simca))

    def score(self, model: 'Model', measurement: 'Measurement') -> float:
        """Returns a models score, evaluated against a _labelled_ measurement (throws/undefined if unlabelled)"""
        simca : Simca = self.__load_model(model)
        return simca.score(measurement.model_input(), measurement.model_target())

    def predict(self, model: 'Model', measurement: 'Measurement') -> np.ndarray:
        """Returns a models prediction of a measurement"""
        simca : Simca = self.__load_model(model)
        return simca.predict(measurement.model_input())

    def train(self,
              model: 'Model',
              measurements: list['Measurement'],
              max_iterations: int,
              max_seconds: int) -> tuple[ModelStorageType, float]:
        """Trains a model, returning the new model with its score"""
        X_concat: np.ndarray = np.concatenate([m.model_input() for m in measurements], axis=0)
        y_concat: np.ndarray = np.concatenate([m.model_target() for m in measurements], axis=0)
        
        one_class_indices: np.ndarray = np.argwhere(np.where(y_concat == 1.0, y_concat, 0.0 )).flatten()
        X_one_class = X_concat[one_class_indices,:]  

        # generate new model with old parameters but new data
        simca_current = self.__load_model(model)
        simca_new = Simca.generate(X_one_class, simca_current.parameters)
        
        # score it
        score = sum(simca_new.score(m.model_input(), m.model_target()) for m in measurements) / len(measurements)
        return (self.__get_model_data(simca_new), score)

    def default_data(self,
         nr_features: int = 2,
         parameters: SimcaParameters = SimcaParameters(0.05, 0.01, 3, LimitType.DDMOMENTS, False)) -> ModelStorageType:
        """Returns the data corresponding to a default (trivial) model"""
        data_tivial = np.zeros(shape=[parameters.n_comp,nr_features])
        return self.__get_model_data(Simca.generate(data_tivial, parameters))