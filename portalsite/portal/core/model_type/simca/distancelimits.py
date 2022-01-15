"""
Distance limits are used by simca model to compute the in-class boundaries
"""

# region - imports
# standard
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

# 3rd party
import numpy as np
from scipy import stats

# local
from helpers import nrows, bound

# type hints
if TYPE_CHECKING:
    from simca import SimcaParameters
    from pca import PCAProjection

# endregion


class LimitType(Enum):
    DDROBUST = 1
    DDMOMENTS = 2


@dataclass
class LimitParameters:
    u0: np.ndarray
    Nu: np.ndarray
    nobj: int

    @staticmethod
    def generate(distances: np.ndarray, limit_type: LimitType) -> 'LimitParameters':
        match limit_type:
            case LimitType.DDMOMENTS:
                return LimitParameters._init_ddmoments(distances)
            case LimitType.DDROBUST:
                return LimitParameters._init_ddrobuts(distances)
            case _:
                raise NotImplementedError("limit type not supported (during init of limit parameters")

    @staticmethod
    def _init_ddmoments(distances: np.ndarray):
        u0 = np.mean(distances, 0)
        Nu = 2 * (u0 / np.std(distances, 0, ddof=1))**2
        return LimitParameters(u0, Nu, nrows(distances))

    @staticmethod
    def _init_ddrobuts(distances: np.ndarray):
        Mu = np.median(distances, 0)
        Su = (  # compute IQR = interquartile range
            np.percentile(distances, 75, axis=0, interpolation='midpoint')
            - np.percentile(distances, 25, axis=0, interpolation='midpoint')
        )
        # must ensure Nu >= 1, since we take a log and then a square root
        temp = bound(2.68631 / (Su / Mu), lower=1.0)
        # but it is not clear to me why we need to bound at 100 here??

        Nu = bound(np.round(np.exp((1.380948 * np.log(temp)) ** 1.185785)), upper=100.0)
        u0 = 0.5 * Nu * (
            Mu / stats.chi2.ppf(0.50, Nu) + Su / (stats.chi2.ppf(0.75, Nu) - stats.chi2.ppf(0.25, Nu)))
        return LimitParameters(u0, Nu, nrows(distances))


@dataclass
class Limits:
    extremes: np.ndarray
    """critical limits for extremes"""
    outliers: np.ndarray
    """critical limits for outliers"""
    mean: np.ndarray
    """"mean value for corresponding distance (or its robust estimate in case of "ddrobust")"""
    dof: np.ndarray
    """degrees of freedom"""

# ' The limits can be accessed as fields of model objects: \code{$Qlim} and \code{$T2lim}. Each
# ' is a matrix with four rows and \code{ncomp} columns. First row contains critical limits for
# ' extremes, second row - for outliers, third row contains mean value for corresponding distance
# ' (or its robust estimate in case of \code{lim.type = "ddrobust"}) and last row contains the
# ' degrees of freedom.


@dataclass
class DistanceLimits:
    parameters: 'SimcaParameters'
    """simca parameters used to generate the limits"""
    Q: Limits
    """limits of the squared orthogonal distance"""
    T2: Limits
    """limits of the score distance"""
    Q_params: LimitParameters
    """parameters used to compute the squared orthogonal distance"""
    T2_params: LimitParameters
    """parameters used to compute the score distance"""

    @staticmethod
    def generate(
            projection: 'PCAProjection',
            parameters: 'SimcaParameters') -> 'DistanceLimits':

        distance_limits = DistanceLimits(parameters,
                                         None,
                                         None,
                                         LimitParameters.generate(projection.distances.Q, parameters.limit_type),
                                         LimitParameters.generate(projection.distances.T2, parameters.limit_type))
        # Note: datadriven limits of each distance depends on the parameters of *both* distances
        if parameters.limit_type in (LimitType.DDROBUST, LimitType.DDMOMENTS):
            distance_limits.init_datadriven_limits()
        else:
            raise NotImplementedError("limit type not supported (during init of distance limits")

        return distance_limits

    def init_datadriven_limits(self):

        Q_params = self.Q_params
        T2_params = self.T2_params

        # bounds of [1, 250] was copied from mdatools - not sure why this is here??
        Nq = bound(np.round(Q_params.Nu), 1, 250)
        Nh = bound(np.round(T2_params.Nu), 1, 250)

        dd_extremes = stats.chi2.ppf(1 - self.parameters.alpha, Nq + Nh),
        dd_outliers = stats.chi2.ppf((1 - self.parameters.gamma)**(1/Q_params.nobj), Nq + Nh)

        self.Q = Limits(
            dd_extremes / Nq * Q_params.u0,
            dd_outliers / Nq * Q_params.u0,
            Q_params.u0,
            Nq
        )

        self.T2 = Limits(
            dd_extremes / Nh * T2_params.u0,
            dd_outliers / Nh * T2_params.u0,
            T2_params.u0,
            Nh
        )

    def get_probabilities(self, projection: 'PCAProjection') -> np.ndarray:
        """
        Computes probability for every object being from the same population as the calibration set, 
        based on the orthogonal and score distances.
        """

        if (self.parameters.limit_type is not LimitType.DDMOMENTS
                and self.parameters.limit_type is not LimitType.DDROBUST):
            raise NotImplementedError("limit type not supported")

        probabilities = np.empty(shape=projection.scores.shape)  # size: data_rows x n_comp

        for i in range(projection.n_comp):
            h = projection.distances.T2[:, i]
            h0 = self.T2.mean[i]
            Nh = np.round(self.T2.dof[i])

            q = projection.distances.Q[:, i]
            q0 = self.Q.mean[i]
            Nq = np.round(self.Q.dof[i])

            temp = stats.chi2.cdf(Nh * h / h0 + Nq * q / q0, Nh + Nq)
            p = 0.5*(1 - temp)/self.parameters.alpha
            probabilities[:, i] = bound(p, upper=1)

        return probabilities
