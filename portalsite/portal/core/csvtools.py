"""Data parsers for uploaded measurements"""
import csv
import json
from dataclasses import dataclass

from django.core.files.uploadedfile import UploadedFile
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

class CsvParser:
    """Wrapper, combining django.core.files.uploadedfile with csv.DictReader"""

    @staticmethod
    def read(file: UploadedFile) -> CsvContent:
        """Read the uploaded file and return the content"""
        # validation
        if(file.multiple_chunks()):
            raise Exception("File to large too handle (multiple_chunks expected)")

        # read data
        file.open()
        reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        headers = list(reader.fieldnames)
        rows = [list(row.values()) for row in reader]
        file.close()

        return CsvContent(headers, rows)

class NumericCsvValidator:

    @classmethod
    def is_float(cls, text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    @classmethod
    def validate(cls, json_data: str) -> bool:
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
