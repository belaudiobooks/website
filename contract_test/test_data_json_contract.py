import json

import requests
from jsonschema import validate


def _get_instance():
    return requests.get("https://audiobooks.by/data.json").json()


def _get_schema():
    with open("audiobooks.schema.json", "r") as f:
        return json.load(f)


def test_mytest():
    validate(instance=_get_instance(), schema=_get_schema())
