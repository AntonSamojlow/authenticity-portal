"""Data parsers for uploaded measurements"""
import csv
import json
from django.core.files.uploadedfile import UploadedFile

class CsvParser:

    @staticmethod
    def to_json(file: UploadedFile) -> str:

        # validation
        if(file.multiple_chunks()):
            raise Exception("File to large handle (multiple_chunks expected)")

        # read data
        file.open()
        reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        headers = list(reader.fieldnames)
        rows = [list(row.values()) for row in reader]
        file.close()

        # return as json
        json_dict = {
            "object_type" : 'csv_content',
            "headers" : headers,
            "rows": rows
        }
        return json.dumps(json_dict)
