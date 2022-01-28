'''
Runs server using tmp sqlite3 database and loads data from dump object.
'''

from collections import defaultdict
import subprocess
import os
from tabnanny import verbose
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
        # Fast but non-working way of adding data as relations between models get lost
        # for some reason.
        # https://stackoverflow.com/questions/19306807/django-fixture-loading-very-slow
        # with open(os.path.join(data_dir, 'data.json'), encoding='utf8') as f:
        #     deserialized = django.core.serializers.deserialize('json', f)
        #     obj_dict = defaultdict(list)
        #     # organize by model class
        #     for item in deserialized:
        #         obj = item.object
        #         obj_dict[obj.__class__].append(obj)

        #     for cls, objs in obj_dict.items():
        #         print(f'Adding models {cls}')
        #         cls.objects.bulk_create(objs)
        print('Completed!')
