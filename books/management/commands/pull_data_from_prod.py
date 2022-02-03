'''
Pulls data and images from production to local repo.
'''

from itertools import chain
import subprocess
import os
from django.core.management.base import BaseCommand
from django.conf import settings
import django

from books.models import Book, Link, LinkType, Person, Tag


class Command(BaseCommand):
    help = 'Pulls data and images from production to local repo.'

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
        for dir in ['covers', 'photos', 'icons']:
            full_dir = os.path.join(data_dir, dir)
            print(f'Pulling images to {dir}')
            subprocess.run([
                'gsutil', '-m', 'rsync', '-d', f'gs://books_media/{dir}',
                full_dir
            ],
                           check=True)

        print('Dumping data from DB.')

        all_people = Person.objects.all()
        all_books = Book.objects.all().prefetch_related(
            'authors', 'narrators', 'translators', 'tag')
        all_link_types = LinkType.objects.all()
        all_links = Link.objects.all()
        all_tags = Tag.objects.all()
        all_objects = list(
            chain(all_people, all_books, all_link_types, all_tags, all_links))
        with open(os.path.join(data_dir, 'data.json'), 'w',
                  encoding='utf8') as f:
            django.core.serializers.serialize('json',
                                              all_objects,
                                              indent=2,
                                              stream=f)
        print('Completed!')
