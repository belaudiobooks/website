'''
See Command desription.
'''

import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    '''See help.'''

    help = 'Initializes default DB using data from "data" submodule.'

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        print(f'Using database {db_path}')
        call_command('makemigrations')
        call_command('migrate', 'books', 'zero')
        call_command('migrate', 'user', 'zero')
        call_command('migrate')
        call_command('loaddata', 'data/data.json')
        print('Completed!')
