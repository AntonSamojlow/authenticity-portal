# standard
from abc import ABC, abstractmethod
from typing import TypeAlias
from json import loads, dumps

# 3rd party
from numpy import ndarray, asarray
from django.core.files.uploadedfile import UploadedFile

# local
from .csvtools import CsvParser, NumericCsvValidator
from .dataclasses import ValidationResult, CsvContent


DataStorageType: TypeAlias = str
"""Format/type used to store the data in the database."""


class DataHandler(ABC):
    """Tooling to validate and transform measurement data which is assumed to be of the type 'Source'"""
    
    @property
    @abstractmethod
    def lookup_id(self) -> str:
        """Identifier used in internal dictionaries - maximal length 10"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns a *short, concise* display name of the handler"""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the handler and its source data, possbily refering to external docs"""

    @abstractmethod
    def validate(self, data: DataStorageType) -> list[ValidationResult]:
        """Validate the data"""

    @abstractmethod
    def load_from_file(self, file: UploadedFile) -> DataStorageType:
        """ ... """

    @abstractmethod
    def to_json(self, data: DataStorageType, indent=None) -> str:
        """Returns the data formatted to json"""

    @abstractmethod
    def to_displaytext(self, data: DataStorageType) -> str:
        """Returns the data formatted as text to be displayed"""

    @abstractmethod
    def to_model_input(self, data: DataStorageType) -> ndarray:
        """Returns the model input part of the data as numpy array, suitable for scroing and training"""
    
    @abstractmethod
    def to_model_target(self, data: DataStorageType) -> ndarray:
        """Returns the model target (or 'label') of the data as numpy array, suitable for training"""

class NumericCsvHandler(DataHandler):
    """Simple data type for development and testing.\nThe target values are assumed to be within the first column"""

    @property
    def lookup_id(self) -> str:
        return "NumericCsv"
    
    @property
    def name(self) -> str:
        return "NumericCsvHandler"

    @property
    def description(self) -> str:
        return self.__doc__

    def validate(self, data: DataStorageType) -> list[ValidationResult]:
        """Validate the data meets requirements"""
        return NumericCsvValidator.validate(CsvContent.from_json(data))

    def load_from_file(self, file: UploadedFile) -> DataStorageType:
        """Tries to read data from file (without validation)."""
        return CsvParser.read(file).to_json()

    def to_json(self, data: DataStorageType, indent=None) -> str:
        """Returns the data formatted to json"""
        return dumps(loads(data), indent=indent)

    def to_displaytext(self, data: DataStorageType) -> str:
        """Returns the data formatted as text to be displayed"""
        return dumps(loads(data), indent=2)

    def to_model_input(self, data: DataStorageType) -> ndarray:
        """Returns the model input part of the data as numpy array, suitable for scroing and training."""
        model_input = [[float(val) for val in row[1:]] for row in CsvContent.from_json(data).rows]
        return asarray(model_input)

    def to_model_target(self, data: DataStorageType) -> ndarray:
        """Returns the model target (or 'label') of the data as numpy array, suitable for training"""
        model_target = [float(row[0]) for row in CsvContent.from_json(data).rows]
        return asarray(model_target)