from dataclasses import dataclass
from typing import Literal
from serializer import ArraySerializer, DistanceLimitsSerializer, LimitsSerializer, PCAProjectionSerializer, PCASerializer, SimcaParametersSerializer, SimcaSerializer

import numpy as np
from simca import LimitType, Simca, SimcaParameters
from json import dumps, loads

x_iris_versicola = np.asarray([
    [7,3.2,4.7,1.4],
    [6.9,3.1,4.9,1.5],
    [6.5,2.8,4.6,1.5],
    [6.3,3.3,4.7,1.6],
    [6.6,2.9,4.6,1.3],
    [5,2,3.5,1],
    [6,2.2,4,1],
    [5.6,2.9,3.6,1.3],
    [5.6,3,4.5,1.5],
    [6.2,2.2,4.5,1.5],
    [5.9,3.2,4.8,1.8],
    [6.3,2.5,4.9,1.5],
    [6.4,2.9,4.3,1.3],
    [6.8,2.8,4.8,1.4],
    [6,2.9,4.5,1.5],
    [5.5,2.4,3.8,1.1],
    [5.8,2.7,3.9,1.2],
    [5.4,3,4.5,1.5],
    [6.7,3.1,4.7,1.5],
    [5.6,3,4.1,1.3],
    [5.5,2.6,4.4,1.2],
    [5.8,2.6,4,1.2],
    [5.6,2.7,4.2,1.3],
    [5.7,2.9,4.2,1.3],
    [5.1,2.5,3,1.1]
    ])

parameters = SimcaParameters(0.05, 0.01, 3, LimitType.DDROBUST, False)

data_tivial = np.zeros(shape=[2,2])

model = Simca.generate(data_tivial, parameters)
print(model.pca)

