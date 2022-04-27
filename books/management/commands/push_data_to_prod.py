'''
Pushes books data and images to production.
'''

import datetime
import os
import subprocess
import tempfile
from typing import Iterable
from django.db import models
from django.core.management.base import BaseCommand
from django.core.management import call_command
import django

from books.models import Book, Link, LinkType, Narration, Person, Tag

REMOTE_DB = 'remote'


def bulk_create_manytomany_relations(model_from, field_name: str,
                                     model_from_name: str, model_to_name: str,
                                     models: Iterable[models.Model]):
    '''See https://stackoverflow.com/a/62658821'''
    through_objs = []
    for model in models:
        for sec_model in getattr(model, field_name).all():
            model_id = model.uuid if hasattr(model, 'uuid') else model.id
            sec_model_id = sec_model.uuid if hasattr(sec_model,
                                                     'uuid') else sec_model.id

            through_objs.append(
                getattr(model_from, field_name).through(
                    **{
                        f"{model_from_name.lower()}_id": model_id,
                        f"{model_to_name.lower()}_id": sec_model_id,
                    }))
    getattr(
        model_from,
        field_name).through.objects.using(REMOTE_DB).bulk_create(through_objs)


class Command(BaseCommand):
    '''See module docs.'''
    help = 'Pushes books data and images to production.'

    def handle(self, *args, **options):

        last_pull_file = os.path.join(tempfile.gettempdir(),
                                      'audiobooks_last_pull')
        assert os.path.exists(
            last_pull_file
        ), f'File {last_pull_file} is missing. Make sure you ran `pull_data_from_prod` command first to ensure you do not override prod data.'
        with open(last_pull_file, 'r', encoding='utf8') as f:
            last_update = datetime.datetime.fromisoformat(f.read())
            diff_min = (datetime.datetime.now() -
                        last_update).total_seconds() / 60
            max_diff_min = 5
            if max_diff_min < diff_min:
                answer = input(
                    'Last sync  was {diff_min} minutes ago. Are you sure you want to continue? yes/no\n'
                )
                if answer != 'yes':
                    return
        try:
            django.db.connections[REMOTE_DB].ensure_connection()
        except django.db.utils.OperationalError:
            print(
                'Cannot connect to DB. Make sure you are running\n' +
                'cloud_sql_proxy -instances="audiobooksbysite:europe-west1:' +
                'audiobooks-prod"=tcp:5432')
            return

        for dir in ['covers', 'photos', 'icons']:
            full_dir = os.path.join('data', dir)
            print(f'Pushing {dir}')
            subprocess.run(
                ['gsutil', '-m', 'rsync', full_dir, f'gs://books_media/{dir}'],
                check=True)

        print('Initializing local DB')
        call_command('init_db_with_data')

        print('Pushing data to remote DB')
        call_command('migrate', 'books', 'zero', database=REMOTE_DB)
        call_command('migrate', 'books', database=REMOTE_DB)

        print('Creating people...')
        Person.objects.using(REMOTE_DB).bulk_create(Person.objects.all())

        print('Creating tags...')
        Tag.objects.using(REMOTE_DB).bulk_create(Tag.objects.all())

        print('Creating books...')
        books = Book.objects.all().prefetch_related('authors', 'tag',
                                                    'translators')
        Book.objects.using(REMOTE_DB).bulk_create(books)
        Book.objects.using(REMOTE_DB).bulk_update(
            Book.objects.all().prefetch_related('authors', 'tag',
                                                'translators'), ['added_at'])
        bulk_create_manytomany_relations(Book, 'authors', 'book', 'person',
                                         books)
        bulk_create_manytomany_relations(Book, 'translators', 'book', 'person',
                                         books)
        bulk_create_manytomany_relations(Book, 'tag', 'book', 'tag', books)

        print('Creating narrations...')
        narrations = Narration.objects.all().prefetch_related(
            'book', 'narrators')
        Narration.objects.using(REMOTE_DB).bulk_create(narrations)
        bulk_create_manytomany_relations(Narration, 'narrators', 'narration',
                                         'person', narrations)

        print('Creating link types...')
        LinkType.objects.using(REMOTE_DB).bulk_create(LinkType.objects.all())

        print('Creating links...')
        Link.objects.using(REMOTE_DB).bulk_create(Link.objects.all())
        print('Completed!')
