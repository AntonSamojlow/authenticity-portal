"""Generic methods"""
# region - imports
# standard
import numpy as np

# 3rd party

# local

# type hints

# endregion


def nrows(matrix: np.ndarray) -> int:
    return matrix.shape[0]


def ncols(matrix: np.ndarray) -> int:
    return matrix.shape[1]


def bound(array: np.ndarray, lower=None, upper=None) -> np.ndarray:
    if lower:
        array = np.where(array >= lower, array, lower)
    if upper:
        array = np.where(array <= upper, array, upper)

    return array
