"""
Custom serializsation tools to help expose, save and restore simca models as JSON text
"""
# region - imports
# standard

# 3rd party
import numpy as np

# local
from .simca import Simca, SimcaParameters, LimitType
from .pca import PCA, PCAProjection
from .distancelimits import DistanceLimits, LimitParameters, Limits


# type hints

# endregion

None_dict = {'object_type': 'None'}


class CustomSerializer:
    """
    Base class for (de)serialization of custom types from/to json-compatible dictionaries, providing type validation.
    """

    dict_type_key = 'object_type'

    def __init__(self, object_type: type, type_string: str = None) -> None:
        self.object_type = object_type
        self.type_string = type(object_type).__name__ if type_string is None else type_string

    def init_dict(self, object_to_serialize) -> dict:
        """
        Returrns a dictionary with entry for key `CustomSerializer.dict_key` preset.
        Raises TypeError if the objects type is unexpected.
        """
        if not type(object_to_serialize) is self.object_type:
            raise TypeError(
                f"can not serialize object of type '{type(object_to_serialize)},' expected type {self.object_type}")
        return {CustomSerializer.dict_type_key: self.type_string}

    def validate_dict(self, json_dict) -> None:
        """
        Raises ValueError if `CustomSerializer.dict_key` is not in `json_dict` or if its value is unexpected.
        """
        if CustomSerializer.dict_type_key not in json_dict:
            raise ValueError("can not recognize objecttype")

        if json_dict[CustomSerializer.dict_type_key] != self.type_string:
            raise ValueError(f"wrong object type '{json_dict['object_type']}', expected {self.object_type}")

        return True


class ArraySerializer(CustomSerializer):
    """
    Responsible for (de) serialization of numpy arrays from/to json-compatible dictionaries
    """

    def __init__(self) -> None:
        super().__init__(np.ndarray, type_string='numpy.ndarray')

    def to_dict(self, array: np.ndarray) -> dict:
        if array is None:
            return None_dict
        json_dict = self.init_dict(array)
        json_dict.update({
            'values': array.tolist()
        })
        return json_dict

    def from_dict(self, json_dict: dict) -> np.ndarray:
        if json_dict == None_dict:
            return None
        self.validate_dict(json_dict)
        return np.asarray(json_dict['values'])


class SimcaParametersSerializer(CustomSerializer):
    """
    Responsible for (de) serialization of numpy arrays from/to json-compatible dictionaries
    """

    def __init__(self) -> None:
        super().__init__(SimcaParameters, type_string='simca_parameters')

    def to_dict(self, parameters: SimcaParameters) -> dict:
        json_dict = self.init_dict(parameters)
        json_dict.update({
            'alpha':  parameters.alpha,
            'gamma': parameters.gamma,
            'n_comp': parameters.n_comp,
            'limit_type': parameters.limit_type.name,
            'scale': parameters.scale
        })
        return json_dict

    def from_dict(self, json_dict: dict) -> SimcaParameters:
        self.validate_dict(json_dict)
        return SimcaParameters(
            float(json_dict['alpha']),
            float(json_dict['gamma']),
            int(json_dict['n_comp']),
            LimitType[json_dict['limit_type']],
            bool(json_dict['scale'])
        )


class PCASerializer(CustomSerializer):
    """
    Responsible for (de) serialization of pca data from/to json-compatible dictionaries
    """

    arrayserializer = ArraySerializer()

    def __init__(self) -> None:
        super().__init__(PCA, type_string='PCA')

    def to_dict(self, pca: PCA) -> dict:
        json_dict = self.init_dict(pca)
        json_dict.update({
            'covariance': self.arrayserializer.to_dict(pca.covariance),
            'eigenvalues': self.arrayserializer.to_dict(pca.eigenvalues),
            'eigenvectors': self.arrayserializer.to_dict(pca.eigenvectors),
            'matrix': self.arrayserializer.to_dict(pca.matrix),
            'bias': pca.bias
        })
        return json_dict

    def from_dict(self, json_dict: dict) -> PCA:
        self.validate_dict(json_dict)
        return PCA(
            self.arrayserializer.from_dict(json_dict['matrix']),
            self.arrayserializer.from_dict(json_dict['covariance']),
            self.arrayserializer.from_dict(json_dict['eigenvalues']),
            self.arrayserializer.from_dict(json_dict['eigenvectors']),
            bool(json_dict['bias'])
        )


class PCAProjectionSerializer(CustomSerializer):
    """
    Responsible for (de) serialization of pca projection data from/to json-compatible dictionaries
    """
    arrayserializer = ArraySerializer()

    def __init__(self) -> None:
        super().__init__(PCAProjection, type_string='PCA_projection')

    def to_dict(self, projection: PCAProjection) -> dict:
        if projection is None:
            return None_dict
        json_dict = self.init_dict(projection)
        json_dict.update({
            # we skip pcas here: we only intend to serialize simca models, which already serialize their own pca copy
            'pca':  "NOT SERIALIZED",
            'distances': {
                'Q': self.arrayserializer.to_dict(projection.distances.Q),
                'T2': self.arrayserializer.to_dict(projection.distances.T2),
            },
            'scores':  self.arrayserializer.to_dict(projection.scores),
            'residuals': self.arrayserializer.to_dict(projection.residuals),
        })
        return json_dict

    # we require passing the PCA from the parent deserialization call (see also to_dict above)
    def from_dict(self, json_dict: dict, pca: PCA) -> PCAProjection:
        if json_dict == None_dict:
            return None
        self.validate_dict(json_dict)
        return PCAProjection(
            self.arrayserializer.from_dict(json_dict['scores']),
            self.arrayserializer.from_dict(json_dict['residuals']),
            pca,
            PCAProjection.Distances(
                self.arrayserializer.from_dict(json_dict['distances']['Q']),
                self.arrayserializer.from_dict(json_dict['distances']['T2']),
            )
        )


class LimitsSerializer(CustomSerializer):
    """
    Responsible for (de) serialization of limits from/to json-compatible dictionaries
    """
    arrayserializer = ArraySerializer()

    def __init__(self) -> None:
        super().__init__(Limits, type_string='limits')

    def to_dict(self, limits: Limits) -> dict:
        json_dict = self.init_dict(limits)
        json_dict.update({
            'dof': self.arrayserializer.to_dict(limits.dof),
            'mean': self.arrayserializer.to_dict(limits.mean),
            'outliers': self.arrayserializer.to_dict(limits.outliers),
            'extremes': self.arrayserializer.to_dict(limits.extremes),
        })
        return json_dict

    def from_dict(self, json_dict: dict) -> Limits:
        self.validate_dict(json_dict)
        return Limits(
            self.arrayserializer.from_dict(json_dict['extremes']),
            self.arrayserializer.from_dict(json_dict['outliers']),
            self.arrayserializer.from_dict(json_dict['mean']),
            self.arrayserializer.from_dict(json_dict['dof'])
        )


class DistanceLimitsSerializer(CustomSerializer):
    """
    Responsible for (de) serialization of simca limits from/to json-compatible dictionaries
    """
    arrayserializer = ArraySerializer()
    limitsserializer = LimitsSerializer()

    def __init__(self) -> None:
        super().__init__(DistanceLimits, type_string='distance_limits')

    def to_dict(self, limits: DistanceLimits) -> dict:
        json_dict = self.init_dict(limits)
        json_dict.update({
            'Q': self.limitsserializer.to_dict(limits.Q),
            'T2': self.limitsserializer.to_dict(limits.T2),
            # we skip pcas here: we only intend to serialize simca models, which already serialize their own pca copy
            'parameters': "NOT SERIALIZED",
            'Q_params': {
                'u0': self.arrayserializer.to_dict(limits.Q_params.u0),
                'Nu': self.arrayserializer.to_dict(limits.Q_params.Nu),
                'nobj': limits.Q_params.nobj,
            },
            'T2_params': {
                'u0': self.arrayserializer.to_dict(limits.T2_params.u0),
                'Nu': self.arrayserializer.to_dict(limits.T2_params.Nu),
                'nobj': limits.T2_params.nobj,
            }
        })
        return json_dict

    def from_dict(self, json_dict: dict, parameters: SimcaParameters) -> DistanceLimits:
        self.validate_dict(json_dict)
        return DistanceLimits(parameters,
                              self.limitsserializer.from_dict(json_dict['Q']),
                              self.limitsserializer.from_dict(json_dict['T2']),
                              LimitParameters(
                                  self.arrayserializer.from_dict(json_dict['Q_params']['u0']),
                                  self.arrayserializer.from_dict(json_dict['Q_params']['Nu']),
                                  int(json_dict['Q_params']['nobj'])
                              ),
                              LimitParameters(
                                  self.arrayserializer.from_dict(json_dict['T2_params']['u0']),
                                  self.arrayserializer.from_dict(json_dict['T2_params']['Nu']),
                                  int(json_dict['T2_params']['nobj']),
                              ))


class SimcaSerializer(CustomSerializer):
    """
    Responsible for (de) serialization of simca models from/to json-compatible dictionaries
    """

    pcaserializer = PCASerializer()
    parametersserializer = SimcaParametersSerializer()
    arrayserializer = ArraySerializer()
    pcaprojectionserializer = PCAProjectionSerializer()
    distancelimitsserializer = DistanceLimitsSerializer()

    def __init__(self) -> None:
        super().__init__(Simca, type_string='Simca')

    def to_dict(self, simca: Simca) -> dict:
        json_dict = self.init_dict(simca)
        json_dict.update({
            'pca': self.pcaserializer.to_dict(simca.pca),
            'parameters': self.parametersserializer.to_dict(simca.parameters),
            'preprocessing_mean': self.arrayserializer.to_dict(simca.preprocessing_mean),
            'preprocessing_std': self.arrayserializer.to_dict(simca.preprocessing_std),
            'data': self.arrayserializer.to_dict(simca.data),
            'calibration_result': self.pcaprojectionserializer.to_dict(simca.calibration_result),
            'test_result': self.pcaprojectionserializer.to_dict(simca.test_result),
            'limit': self.distancelimitsserializer.to_dict(simca.limits),
        })
        return json_dict

    def from_dict(self, json_dict) -> Simca:
        self.validate_dict(json_dict)
        pca = self.pcaserializer.from_dict(json_dict['pca'])
        parameters = self.parametersserializer.from_dict(json_dict['parameters'])
        return Simca(
            self.arrayserializer.from_dict(json_dict['data']),
            self.arrayserializer.from_dict(json_dict['preprocessing_mean']),
            self.arrayserializer.from_dict(json_dict['preprocessing_std']),
            pca,
            self.pcaprojectionserializer.from_dict(json_dict['calibration_result'], pca),
            self.pcaprojectionserializer.from_dict(json_dict['test_result'], pca),
            self.distancelimitsserializer.from_dict(json_dict['limit'], parameters),
            parameters
        )
