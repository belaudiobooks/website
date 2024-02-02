"""
Runs server using tmp sqlite3 database and loads data from dump object.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    """Initializes server from data repo and runs it using local sqlite database."""

    help = "Initializes DB in tmp file with data provided in dump and runs server on that db."

    def handle(self, *args, **options):
        call_command(
            "init_db_with_data",
            "--skip-if-exists",
            create_superuser="admin@example.com",
        )
        call_command("runserver")
