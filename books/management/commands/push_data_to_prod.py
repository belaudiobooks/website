'''
Pushes books data and images to production.
'''

import subprocess
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import django


class Command(BaseCommand):
    help = 'Pushes books data and images to production.'

    def handle(self, *args, **options):
        try:
            django.db.connection.ensure_connection()
        except django.db.utils.OperationalError:
            print(
                'Cannot connect to DB. Make sure you are running\n' +
                'cloud_sql_proxy -instances="audiobooksbysite:europe-west1:' +
                'audiobooks-prod"=tcp:5432')
            return
        db_path = settings.DATABASES['default']['NAME']
        data_dir = os.environ.get('BOOKS_DATA_DIR', None)
        if data_dir is None:
            print('Must provide BOOKS_DATA_DIR variable that points to ' +
                  'location of audiobooks/data repo on local disk.')
            return
        print(f'Using database {db_path}')
        call_command('makemigrations')
        call_command('migrate', 'books', 'zero')
        call_command('migrate', 'books')
        for dir in ['covers', 'photos', 'icons']:
            full_dir = os.path.join(data_dir, dir)
            print(f'Pushing {dir}')
            subprocess.run(
                ['gsutil', '-m', 'rsync', full_dir, f'gs://books_media/{dir}'],
                check=True)

        print('Uploading data to DB. It is going to be slow...')
        call_command('loaddata',
                     os.path.join(data_dir, 'data.json'),
                     verbosity=3)
        print('Completed!')
