
# region - imports
# standard
from dataclasses import dataclass, field

# 3rd party
import numpy as np

# local
from .pca import PCA, PCAProjection
from .distancelimits import LimitType, DistanceLimits

# type hints

# endregion

@dataclass(frozen=True)
class SimcaParameters:
    alpha: int
    gamma: int
    n_comp: int
    limit_type: LimitType
    scale: bool
    """
    Whether to standardize before performing the PCA.
    (Equivalent to decomposing the correlation instead of the covariance matrix).
    """
@dataclass
class Simca:
    data: np.ndarray
    preprocessing_mean: np.ndarray
    preprocessing_std: np.ndarray
    pca: PCA
    calibration_result: PCAProjection
    test_result: PCAProjection
    limits: DistanceLimits
    parameters: SimcaParameters
    _parameters: SimcaParameters = field(init=False, repr=False)

    @staticmethod
    def generate(one_class_data: np.ndarray, parameters: SimcaParameters, 
        test_matrix: np.ndarray = None) -> 'Simca':
    
        # store unprocessed data
        data = one_class_data.astype(float)

        # compute and store preprocessing parameters
        preprocessing_mean = np.mean(data, 0)
        preprocessing_std = np.std(data, 0, ddof = 1) if parameters.scale else None
        
        # intialize fields that are required to generate the subsequent fields
        simca = Simca(data, 
            preprocessing_mean, 
            preprocessing_std, 
            None, 
            None, 
            None,
            None,
            parameters)
        simca.pca = PCA.generate(simca._preprocess(data))
        simca.recalibrate(parameters)
   
        # TODO: test-prediction, (cross)-validation?
        simca.test_result = simca.pca.project(test_matrix, simca.parameters.n_comp) if test_matrix else None
        return simca
    @property
    def parameters(self) -> SimcaParameters:
        return self._parameters

    # we clean up any attempt to set invalid parameters
    def _cleaned_parameters(self, parameters: SimcaParameters) -> SimcaParameters:
        alpha = float(max(0.0, min(parameters.alpha, 1.0)))
        gamma = float(max(0.0, min(parameters.gamma, 1.0)))
        # note that this might fail if data has not been set yet:
        n_comp = int(max(0, min(parameters.n_comp, 
            self.data.shape[0], 
            self.data.shape[1])))
        if not isinstance(parameters.limit_type, LimitType):
            raise TypeError("limit_type parameter is not recognized")
        return SimcaParameters(alpha, gamma, n_comp, parameters.limit_type, parameters.scale)

    @parameters.setter
    def parameters(self, new_value: SimcaParameters):
        if '_parameters' in self.__dict__ and self._parameters.scale != new_value.scale:
            raise ValueError("changing the scale parameter is not possible")
        self._parameters = self._cleaned_parameters(new_value)

    
    def recalibrate(self, new_parameters: SimcaParameters):
        """
        Adjust the model limits to the provided new parameters and sets the calibration data.
        Note: The PCA and the preprocessing data is not changed.
        """
        new_calibration_result = self.pca.project(self.pca.matrix, new_parameters.n_comp)
        new_limits = DistanceLimits.generate(new_calibration_result, new_parameters)
        # only set values if previous methods concluded to avoid a failed state
        self.parameters = new_parameters
        self.calibration_result = new_calibration_result
        self.limits = new_limits

    def predict_all_components(self, matrix: np.ndarray) -> np.ndarray:
        """
        Computes probabilities for the matrix data (rows) to belong to same class as the calibration data,
        based on its orthogonal and score distances and for *all* computed component choices.

        Returns: Matrix (m x n), where m = rowcount of input matrix, n = `self.parameters.n_comp`  
        """
        projection = self.pca.project(self._preprocess(matrix), self.parameters.n_comp)
        probabilities = self.limits.get_probabilities(projection)
        return probabilities
    
    def predict(self, matrix: np.ndarray, comp_count: int = 0) -> np.ndarray:
        """
        Computes probabilities for the matrix data (rows) to belong to same class as the calibration data,
        based on its orthogonal and score distances.

        Arguments:
            - comp_nr: The desired principal component count. 
            The default of 0 is interpreted as all (maximal nr of) components for which the pca was calculated.
        """
        if (comp_count < 0 or comp_count > self.parameters.n_comp):
            raise ValueError("chosen comp_nr is invalid or incompatible with the model")
        return self.predict_all_components(matrix)[:, comp_count-1]

    def _preprocess(self, matrix: np.ndarray) -> np.ndarray:
        """
        Returns a preprocessed matrix: Centered by the mean and (if enabled) scaled by the standard deviation.
        """
        preprocessed = matrix - self.preprocessing_mean
        if self.parameters.scale:
            preprocessed /= self.preprocessing_std
        return preprocessed
            
    def score(self, matrix: np.ndarray, target_values: np.ndarray, components: int = None) -> float:
        """
        Predicts the matrix and returns the score:= 1 - average(target - predicted)

        Arguments:
            - matrix (ndarray): Data matrix to predict
            - matrix (ndarray): Vector of target values to predict
            - components (int): Number of components to be used for the prediction. 
            If set to None, the value is read from simca parameters.
        """
        if components is None:
            components = self.parameters.n_comp
        
        if (components < 0 or components > self.parameters.n_comp):
            raise ValueError("chosen comp_nr is invalid or incompatible with the model")
        
        predictions = self.predict(matrix, components)
        return float(1.0 - np.mean(np.abs(target_values - predictions)))


   
