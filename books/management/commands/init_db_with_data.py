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

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='Does not creates database if it already exists.',
        )
        parser.add_argument(
            '--create-superuser',
            help=
            'Creates superuser with using given email. Password is read from DJANGO_SUPERUSER_PASSWORD variable',
        )

    def handle(self, *args, **options):
        db_path = settings.DATABASES['default']['NAME']
        if options['skip_if_exists'] and os.path.exists(db_path):
            print(
                f'Not creating database {db_path} as it already exists and --skip-if-exists is enabled.'
            )
            return
        print(f'Creating database {db_path}')
        call_command('makemigrations')
        call_command('migrate', 'books', 'zero')
        call_command('migrate', 'user', 'zero')
        call_command('migrate')
        call_command('loaddata', 'data/data.json')
        if 'create_superuser' in options and options[
                'create_superuser'] is not None:
            superuser_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', None)
            assert superuser_pass, 'DJANGO_SUPERUSER_PASSWORD must be set when using --create-superuser option'
            email = options['create_superuser']
            call_command('createsuperuser', '--no-input', email=email)
            print(f'Create superuser {email} with pass {superuser_pass}')
        print('Completed!')
