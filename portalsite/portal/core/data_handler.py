# standard
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeAlias
from json import loads, dumps

# 3rd party
from numpy import ndarray, asarray
from django.core.files import uploadedfile
from django.core.files.uploadedfile import UploadedFile

# local
from .csvtools import CsvParser, CsvContent, NumericCsvValidator


@dataclass
class ValidationResult:
    failed: bool
    """Whether this validation step failed"""
    name: str
    """Descriptive name of the rule/step being validated"""
    details: str
    """Details, i.p. in case of a failure"""


StorageType: TypeAlias = str
"""Format/type used to store the data in the database."""


class DataHandler(ABC):
    """Tooling to validate and transform measurement data which is assumed to be of the type 'Source'"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns a *short, concise* name of the handler"""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the handler and its source data, possbily refering to external docs"""

    @abstractmethod
    def validate(self, data: StorageType) -> list[ValidationResult]:
        """Validate the data"""

    @abstractmethod
    def load_from_file(self, file: UploadedFile) -> StorageType:
        """ ... """

    @abstractmethod
    def as_json(self, data: StorageType, indent=None) -> str:
        """Returns the data formatted to json"""

    @abstractmethod
    def as_displaytext(self, data: StorageType) -> str:
        """Returns the data formatted as text to be displayed"""

    @abstractmethod
    def as_array(self, data: StorageType) -> ndarray:
        """Returns the data as numpy arrau, i.p. suitable a model input"""


class NumericCsvHandler(DataHandler):
    """Simple data type for development and testing"""

    @property
    def name(self) -> str:
        return "NumericCsvHandler"

    @property
    def description(self) -> str:
        return self.__doc__

    def validate(self, data: StorageType) -> list[ValidationResult]:
        """Validate the data meets requirements"""
        return NumericCsvValidator.validate(data)

    def load_from_file(self, file: UploadedFile) -> StorageType:
        """Tries to read data from file (without validation)."""
        return CsvParser.read(file).to_json()

    def as_json(self, data: StorageType, indent=None) -> str:
        """Returns the data formatted to json"""
        return dumps(loads(data), indent=indent)

    def as_displaytext(self, data: StorageType) -> str:
        """Returns the data formatted as text to be displayed"""
        return dumps(loads(data), indent=2)

    def as_array(self, data: StorageType) -> ndarray:
        """Returns the data as numpy arrau, i.p. suitable a model input"""
        return asarray(CsvContent.from_json(data).rows)
