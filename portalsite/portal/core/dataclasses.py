import json

from dataclasses import dataclass

@dataclass
class ValidationResult:
    success: bool
    """Whether this validation step succeeded"""
    name: str
    """Descriptive name of the rule/step being validated"""
    details: str
    """Details, i.p. in case of a failure"""

@dataclass
class CsvContent:
    """Structured content of a csv file"""
    headers: list[str]
    rows: list[list[str]]

    def to_json(self, indent = None):
        json_dict = {
            "object_type" : 'CsvContent',
            "headers" : self.headers,
            "rows": self.rows
        }
        return json.dumps(json_dict, indent=indent)

    @staticmethod
    def from_json(json_data) -> 'CsvContent':
        json_dict : dict = json.loads(json_data)
        if 'object_type' not in json_dict.keys():
            raise ValueError("Failed to serialize json string as CsvContent: missing 'object_type'")
        if json_dict['object_type'] != 'CsvContent':
            raise ValueError("Failed to serialize json string as CsvContent: 'object_type' does not match")
        return CsvContent(json_dict["headers"], json_dict["rows"])
