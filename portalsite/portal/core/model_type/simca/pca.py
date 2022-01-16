"""Principal Component Analysis, using numpys 'eigenh' decomposition"""
# region - imports
# standard
from dataclasses import dataclass

# 3rd party
import numpy as np

# local
from .helpers import ncols, nrows

# type hints

# endregion


@dataclass
class PCA:
    """
    PCA is the eigenvalue decomposition of the sample matrix covariance (or correlation if scaled).

    It is used to reduce the dimensionality of a problem: `project` a data matrices to subspaces of
    eigenvectors corresponding to the the largest eigenvalues (with largest variance).
    """

    matrix: np.ndarray
    """
    The (preprocessed) matrix that was used for the PCA
    """
    covariance: np.ndarray
    """
    The covariance matrix that was decomposed for the PCA - it equals the correlation matrix if scaled is `True`
    """
    eigenvalues: np.ndarray
    """
    The eigenvalues in descending order
    """
    eigenvectors: np.ndarray  # aka 'loadings'
    """
    The eigenvalues in descending order (of eigenvalues)
    """
    bias: bool
    """
    If bias is `True`, the covariance is normalized by N instead of N-1
    """

    @staticmethod
    def generate(matrix: np.ndarray, bias=False) -> 'PCA':
        """
        Computes the eigenvalue decomposition of the covariance (of the transposed sample matrix).
        Note that the covarience is by definition 'implicitely mean centered'

        arguments:
            - matrix: sample matrix
            - bias (bool): whether to normalize the covariance by N (`True`) or N-1 (`False`)
        """

        # compute and store values
        covariance = np.cov(matrix.T, bias=bias)

        # get eigen decomposition and sort by descending eigenvalues
        # we also force the eigenvalues positive - they might be erroneously negative due to numerical precision limits
        eigenvalues, eigenvectors = np.linalg.eigh(covariance)
        eigenvalues = np.abs(eigenvalues)
        descending_indices = np.argsort(eigenvalues)[::-1]

        return PCA(matrix, covariance, eigenvalues[descending_indices], eigenvectors[:, descending_indices], bias)

    def project(self, matrix: np.ndarray, n_comp: int) -> 'PCAProjection':
        """
        Projects a `matrix` to the space of the `ncomp` largest principal components
        """
        if ncols(matrix) != nrows(self.eigenvectors):
            raise ValueError("Can not apply PCA, matrix dimensions (column count) is incompatible")

        if not isinstance(n_comp, int) or n_comp < 1:
            raise ValueError("N-comp must be a positive integer")

        # select new basis of `n_comp`- many components
        total_comp = len(self.eigenvectors)
        n_comp = min(total_comp, n_comp)
        new_space: np.ndarray = self.eigenvectors[:, :n_comp]

        # compute projection (scores) and residual
        scores = np.matmul(matrix, new_space)
        residual = matrix - np.matmul(scores, new_space.T)
        result = PCAProjection(scores, residual, self, None)

        # compute and set distances on the result object
        self._set_distances(result)

        return result

    def _set_distances(self, pca_result: 'PCAProjection') -> 'PCAProjection.Distances':
        # normalize the scores
        scores_normal = pca_result.scores / np.sqrt(self.eigenvalues[:pca_result.n_comp])

        # distances: matrix of same shape as scores (sample size x n_comp)
        # for each sample (row), compute the diatnce for the one (Q) or all (T2) involved components
        shape = pca_result.scores.shape
        distances = PCAProjection.Distances(
            np.empty(shape=shape, dtype=float),
            np.empty(shape=shape, dtype=float))

        # calculate distances and model power for each possible number of components in model
        n_comp = pca_result.n_comp
        for i in range(0, n_comp):
            res = pca_result.residuals + np.matmul(
                pca_result.scores[:, i+1:n_comp],
                self.eigenvectors[:, i+1:n_comp].T)
            distances.Q[:, i] = np.sum(res**2, 1)
            distances.T2[:, i] = np.sum(scores_normal[:, :i+1]**2, 1)

        pca_result.distances = distances


@dataclass
class PCAProjection:
    """
    Result of 'projecting' a matrix to the space of `n_comp` larges many components
    """
    scores: np.ndarray
    residuals: np.ndarray
    pca: 'PCA'
    distances: 'PCAProjection.Distances'

    @dataclass
    class Distances:
        """
        The calculated distances of a PCA projection
        """
        Q: np.ndarray
        """
        Matrix of orthognal distances:
        Column i holds the squared residual distances to the subspace spanned by the eigenvectors i+1,...,n_comp
        """
        T2: np.ndarray
        """
        Matrix of scores distances:
        Column i holds the (squared) eigenvalue-normalized scores corresponding to eigenvectors 1,...,i
        """

    @property
    def n_comp(self) -> int:
        """
        Number of principal components and dimension of the projected space
        """
        return ncols(self.scores)

    @property
    def n_samples(self) -> int:
        """
        Number of samples (number of score rows)
        """
        return nrows(self.scores)

    @property
    def residual_norm(self) -> float:
        """
        Size of the residual
        """
        return np.linalg.norm(self.residuals)
