"""
Settings to be used by runserver_with_tmp_db command. See README.
This is a hacky way of overriding main settings and changing few params
like database without affecting the main settings.
"""

import tempfile
import os
from booksby.settings import *

_, path = tempfile.mkstemp(
    prefix="tmp_db_",
    suffix=".sqlite3",
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path,
    }
}

assert "BOOKS_DATA_DIR" in os.environ, "Provide BOOKS_DATA_DIR variable when running command. See README."
MEDIA_ROOT = os.environ["BOOKS_DATA_DIR"]
