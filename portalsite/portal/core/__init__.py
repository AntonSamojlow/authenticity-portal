"""
Contains the 'core concepts' of the portal app
"""


from .data_handler import NumericCsvHandler
from .model_type.test_model import TestModelType
from .model_type.linear_regression import LinearRegressionModel
from .model_type.simca_model import SimcaModel
from .named_id_manager import NamedIdManager


NUMERICCSVHANDLER = NumericCsvHandler()
TESTMODELTYPE = TestModelType()
LINEARREGRESSIONMODEL = LinearRegressionModel()
SIMCAMODEL = SimcaModel()

DATAHANDLERS = NamedIdManager([NUMERICCSVHANDLER])

MODELTYPES = NamedIdManager([TESTMODELTYPE,
                             LINEARREGRESSIONMODEL,
                             SIMCAMODEL])
