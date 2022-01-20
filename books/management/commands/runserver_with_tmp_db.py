"""
Runs server using tmp sqlite3 database and loads data from dump object.
"""

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Initializes DB in tmp file with data provided in dump and runs server on that db.'

    def handle(self, *args, **options):
        db_path = settings.DATABASES["default"]["NAME"]
        print(f"Using database {db_path}")
        call_command("makemigrations")
        call_command("migrate")
        data_dir = os.environ["BOOKS_DATA_DIR"]
        call_command("loaddata", os.path.join(data_dir, "data.json"))
        call_command("runserver")
