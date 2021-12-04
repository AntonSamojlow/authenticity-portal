from .data_handler import NumericCsvHandler
from .model_type.test_model import TestModelType
from .model_type.linear_regression import LinearRegressionModel
from .named_id_manager import NamedIdManager

DATAHANDLERS = NamedIdManager([NumericCsvHandler()])

MODELTYPES = NamedIdManager([TestModelType(),
                             LinearRegressionModel()])
