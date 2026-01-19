import unittest
import json

import requests
from jsonschema import validate


class ProductionDataJsonContractTest(unittest.TestCase):

    def get_instance(self):
        return requests.get("https://audiobooks.by/data.json").json()

    def get_schema(self):
        with open("books/tests/schema.data.json", "r") as f:
            return json.load(f)

    def test_contract(self):
        validate(instance=self.get_instance(), schema=self.get_schema())
