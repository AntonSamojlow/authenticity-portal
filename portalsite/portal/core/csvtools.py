"""Data parsers for uploaded measurements"""
import csv

from django.core.files.uploadedfile import UploadedFile
from .dataclasses import CsvContent, ValidationResult

class CsvParser:
    """Wrapper, combining django.core.files.uploadedfile with csv.DictReader"""

    @staticmethod
    def read(file: UploadedFile) -> CsvContent:
        """Read the uploaded file and return the content"""
        # validation
        if file.multiple_chunks():
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
    def validate(cls, csv_content: CsvContent) -> list[ValidationResult]:
        header_count = len(csv_content.headers)
        results = []

        # check headers have text and not pure values
        float_headers = []
        for header in csv_content.headers:
            if NumericCsvValidator.is_float(header):
                float_headers.append(header)
        if len(float_headers) > 0:
            results.append(ValidationResult(False, "Numeric value in header",
                details=f"Found {len(float_headers)} headers with numeric values: {','.join(float_headers)}"))

        # check all rows have float content
        for row_nr in range(len(csv_content.rows)):
            row = csv_content.rows[row_nr]
            if not isinstance(row, list):
                results.append(ValidationResult(False, "Empty row",
                    details=f"Row {row_nr} has no data"))
            elif len(row) != header_count:
                results.append(ValidationResult(False, "Nr of entries is incosistent",
                    details=f"Row {row_nr} has {len(row)} entries, but file has {header_count} headers"))
            else:
                for column_nr in range(len(row)):
                    entry = row[column_nr]
                    if not isinstance(entry, str):
                        # this should not happen, so we throw
                        raise Exception("Expected string - something really bad happened")
                    if not NumericCsvValidator.is_float(entry):
                        results.append(ValidationResult(False, "Not a float",
                            details=f"Row {row_nr}, column {column_nr}: Can not parse '{entry}' as float."))
        return results
