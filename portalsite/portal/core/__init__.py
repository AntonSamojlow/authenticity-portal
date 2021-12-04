from .data_handler import NumericCsvHandler
from .model_type import TestModelType, LinearRegressionModel
from .named_id_manager import NamedIdManager

DATAHANDLERS = NamedIdManager([NumericCsvHandler()])

MODELTYPES = NamedIdManager([TestModelType(),
                             LinearRegressionModel(2),
                             LinearRegressionModel(5)])
