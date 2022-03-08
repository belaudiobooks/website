'''
Runs server using tmp sqlite3 database and loads data from dump object.
'''

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    '''Initializes server from data repo and runs it using local sqlite database.'''

    help = 'Initializes DB in tmp file with data provided in dump and runs server on that db.'

    def handle(self, *args, **options):
        call_command('init_db_with_data')

        superuser_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', None)
        if superuser_pass is None:
            print(
                'Superuser not created. Pass DJANGO_SUPERUSER_PASSWORD=12345 to create superuser'
            )
        else:
            call_command('createsuperuser',
                         '--no-input',
                         email='admin@example.com')
            print(
                f'Create superuser admin@example.com with pass {superuser_pass}'
            )
        call_command('runserver', '--noreload')
