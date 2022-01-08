# standard
from abc import ABC, abstractmethod
from typing import TypeAlias
from json import loads, dumps
from django.core.files.base import ContentFile

# 3rd party
from numpy import ndarray, asarray
from django.core.files.uploadedfile import UploadedFile

# local
from .csvtools import CsvParser, NumericCsvValidator
from .dataclasses import ValidationResult, CsvContent
from .named_id_manager import NamedIdObject

DataStorageType: TypeAlias = str
"""Format/type used to store the data in the database."""


class DataHandler(ABC, NamedIdObject):
    """Tooling to validate and transform measurement data"""
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the handler and its source data, possbily refering to external docs"""

    @abstractmethod
    def validate(self, data: DataStorageType) -> list[ValidationResult]:
        """Validate the data"""

    @abstractmethod
    def load_from_file(self, file: UploadedFile) -> DataStorageType:
        """Tries to read data from file (without validation)."""

    @abstractmethod
    def to_file(self, data: DataStorageType) -> ContentFile:
        """Returns the data formatted to a ContentFile, to be served in a download""" 

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
    def id_(self) -> str:
        return "NumericCsv"
    
    @property
    def name(self) -> str:
        return "NumericCsv"

    @property
    def description(self) -> str:
        return self.__doc__

    def validate(self, data: DataStorageType) -> list[ValidationResult]:
        """Validate the data meets requirements"""
        return NumericCsvValidator.validate(CsvContent.from_json(data))

    def load_from_file(self, file: UploadedFile) -> DataStorageType:
        """Tries to read data from file (without validation)."""
        return CsvParser.read(file).to_json()

    def to_file(self, data: DataStorageType) -> ContentFile:
        """Returns the data formatted to a ContentFile, to be served in a download"""    
        csv = CsvContent.from_json(data)
        contentstring = ",".join(csv.headers)+"\n"
        for row in csv.rows:
            contentstring += ",".join(row)+"\n"
        return ContentFile(contentstring)


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
        