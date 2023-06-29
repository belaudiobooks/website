'''
Pulls data and images from production to local repo.
'''

from itertools import chain
import subprocess
import os
import tempfile
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import django

from books.models import Book, Link, LinkType, Narration, Person, Publisher, Tag

REMOTE_DB = 'remote'


class Command(BaseCommand):
    '''Pulls data and images from production to local repo.'''
    help = 'Pulls data and images from production to local repo.'

    def handle(self, *args, **options):
        try:
            django.db.connections[REMOTE_DB].ensure_connection()
        except django.db.utils.OperationalError:
            print(
                'Cannot connect to DB. Make sure you are running\n' +
                'cloud_sql_proxy -instances="audiobooksbysite:europe-west1:' +
                'audiobooks-prod"=tcp:5432')
            return
        db_path = settings.DATABASES[REMOTE_DB]['NAME']
        print(f'Using database {db_path}')
        for dir in ['covers', 'photos', 'icons', 'logos']:
            full_dir = os.path.join('data', dir)
            print(f'Pulling images to {dir}')
            subprocess.run([
                'gsutil', '-m', 'rsync', '-d', f'gs://books_media/{dir}',
                full_dir
            ],
                           check=True)

        print('Dumping data from DB.')

        all_people = Person.objects.using(REMOTE_DB).all().order_by('uuid')
        all_tags = Tag.objects.using(REMOTE_DB).all()
        all_books = Book.objects.using(REMOTE_DB).all().prefetch_related(
            'authors', 'translators', 'tag').order_by('uuid')
        all_narrations = Narration.objects.using(
            REMOTE_DB).all().prefetch_related('narrators',
                                              'publishers').order_by('uuid')
        all_link_types = LinkType.objects.using(REMOTE_DB).all()
        all_links = Link.objects.using(REMOTE_DB).all().order_by('uuid')
        all_publishers = Publisher.objects.using(REMOTE_DB).all().order_by(
            'uuid')
        all_objects = list(
            chain(all_people, all_tags, all_books, all_narrations,
                  all_link_types, all_links, all_publishers))
        with open('data/data.json', 'w', encoding='utf8') as f:
            django.core.serializers.serialize('json',
                                              all_objects,
                                              indent=2,
                                              stream=f)

        last_pull_file = os.path.join(tempfile.gettempdir(),
                                      'audiobooks_last_pull')
        with open(last_pull_file, 'w', encoding='utf8') as f:
            f.write(datetime.datetime.now().isoformat())
        print('Completed!')
