"""Type validators verify whether json data can be interpreted as specific data type"""

import json
from abc import ABC, abstractmethod

class TypeValidator(ABC):
    """Abstract base class for validation, defines the interface to be used by each data type"""
    @abstractmethod
    def validate(self, json_data: str) -> bool:
        pass


class NumericCsvValidator(TypeValidator):

    @classmethod
    def is_float(cls, text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    def validate(self, json_data: str) -> bool:
        json_dict : dict = json.loads(json_data)
        # try and read the data
        try:
            object_type = str(json_dict["object_type"])
            headers  =  json_dict["headers"]
            rows = json_dict["rows"]
        except KeyError:
            return False

        if(object_type != "csv_content"):
            return False

        column_count = len(headers)

        # check headers have text and  not pure values
        for header in headers:
            if NumericCsvValidator.is_float(header):
                return False

        # check all rows have float content
        for row in rows:
            if not isinstance(row, list) or len(row) != column_count:
                return False
            for entry in row:
                if not (isinstance(entry, str) and NumericCsvValidator.is_float(entry)):
                    return False

        return True
