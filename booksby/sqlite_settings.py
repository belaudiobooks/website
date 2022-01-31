"""
Settings to be used by runserver_with_tmp_db command. See README.
This is a hacky way of overriding main settings and changing few params
like database without affecting the main settings.
"""

import tempfile
import os
from booksby.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(tempfile.gettempdir(), 'audiobooksby.sqlite3'),
    }
}

assert "BOOKS_DATA_DIR" in os.environ, "Provide BOOKS_DATA_DIR variable when running command. See README."
MEDIA_ROOT = os.environ["BOOKS_DATA_DIR"]
