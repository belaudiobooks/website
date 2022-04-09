'''
Script for managing DB data stored in JSON. Managing includes syncing data from
other sources like podcasts, knizhny voz, litres. It also provides script for validating
that data is correct. See SYNC_COMMANDS for various commands.
'''
import os
import sys
from typing import Callable, Dict
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booksby.sqlite_settings')
django.setup()

from django.core import management
from books.models import Book, Person, Tag

from . import sync_yandex, add_durations, sync_add_translations, sync_from_json, sync_kamunikat, sync_knihi_com, sync_knizhny_voz, sync_litres, sync_mininform, sync_podcasts, sync_soundcloud
from data_scripts.books import BooksData


def _initialize_db() -> None:
    management.call_command('makemigrations')
    management.call_command('migrate', 'books', 'zero')
    management.call_command('migrate')
    management.call_command('loaddata', 'data/data.json')


def _dump_db() -> None:
    with open('data/data.json', 'w', encoding='utf8') as f:
        management.call_command('dumpdata', 'books', indent=2, stdout=f)
    management.call_command('loaddata', 'data/data.json')


SYNC_COMMANDS: Dict[str, Callable[[BooksData], None]] = {
    'podcasts': sync_podcasts.run,
    'knizhny_voz': sync_knizhny_voz.run,
    'mininform': sync_mininform.run,
    'from_json': sync_from_json.run,
    'litres': sync_litres.run,
    'soundcloud': sync_soundcloud.run,
    'knihi_com': sync_knihi_com.run,
    'kamunikat': sync_kamunikat.run,
    'add_translations': sync_add_translations.run,
    'add_durations': add_durations.run,
    'yandex': sync_yandex.run,
}


def main() -> None:
    """Run mains"""
    assert len(sys.argv) == 2, 'Must pass sync command to run.'
    command = sys.argv[1]
    if command not in SYNC_COMMANDS:
        available_commands = ', '.join(SYNC_COMMANDS.keys())
        raise ValueError(f'Must pass a command. One of {available_commands}')
    _initialize_db()

    print(f'Running "{command}"')
    data = BooksData(
        people=list(Person.objects.all()),
        books=list(Book.objects.all()),
    )
    SYNC_COMMANDS[command](data)
    _dump_db()


if __name__ == '__main__':
    main()
