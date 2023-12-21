'''
See Command desription.
'''

from datetime import date, timedelta
import os
import shutil
from typing import List
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from books.models import Book, BookStatus, Narration, Person, Publisher, Tag, Link, LinkType, Gender, Language
from django.contrib.auth import get_user_model


def create_book_with_single_narration(
        title: str,
        authors: List[Person] = [],
        translators: List[Person] = [],
        narrators: List[Person] = [],
        tags: List[Tag] = [],
        link_types: List[LinkType] = [],
        language: Language = Language.BELARUSIAN,
        publishers: List[Publisher] = [],
        date=date.today(),
        duration: timedelta = timedelta(hours=1, minutes=15),
        paid: bool = False,
        livelib_url: str = ''
):
    book = Book.objects.create(
        title=title,
        title_ru=f'{title} по-русски',
        description=f'Апісанне кнігі "{title}"',
        status=BookStatus.ACTIVE,
        livelib_url=livelib_url
    )
    book.authors.set(authors)
    book.tag.set(tags)
    narration = Narration.objects.create(
        language=language,
        duration=duration,
        book=book,
        paid=paid,
        date=date,
    )
    narration.narrators.set(narrators)
    narration.translators.set(translators)
    narration.publishers.set(publishers)
    for link_type in link_types:
        narration.links.add(create_link(link_type, narration.book))
    narration.save()
    return book

def fill_with_data():
    tag_proza = Tag.objects.create(name='Сучасная проза', slug='proza')
    tag_classics = Tag.objects.create(name='Класікі беларускай літаратуры', slug='classics')
    tag_children = Tag.objects.create(name='Дзецям і падлеткам', slug='children')

    publisher_audiobooksby = Publisher.objects.create(
        name='adubiobooks.by',
        slug='audiobooksby',
        url='https://audiobooks.by',
        description='Аўдыёкнігі на беларускай мове',
        logo='logos/audiobooksby.png')
    publisher_knizhny_voz = Publisher.objects.create(
        name='Кніжны воз',
        slug='knizhny-voz',
        url='https://knizhnyvoz.com',
        description='Кніжны воз - кнігі для дзяцей і падлеткаў',
        logo='logos/knizhny-voz.jpg')

    person_adam = Person.objects.create(
        name='Адам Адамовіч',
        slug='adam-adamovich',
        description='Біяграфія тут',
        photo='photos/adam.png',
        gender=Gender.MALE)
    person_bahdana = Person.objects.create(
        name='Багдана Багданаўна',
        slug='bahdana-bahdanawna',
        description='Біяграфія Багданы Багданаўны тут',
        photo='photos/bahdana.png',
        gender=Gender.FEMALE)
    person_valer = Person.objects.create(
        name='Валер Валеравіч',
        slug='valer-valeravich',
        gender=Gender.MALE)

    for i in range(6):
        create_book_with_single_narration(
            title=f'Проза {i + 1}',
            tags=[tag_proza],
            authors=[person_adam],
            narrators=[person_bahdana],
            publishers=[publisher_audiobooksby],
        )
        create_book_with_single_narration(
            title=f'Дзіцячая кніга {i + 1}',
            tags=[tag_children],
            authors=[person_bahdana],
            narrators=[person_valer],
            publishers=[publisher_knizhny_voz],
        )
        create_book_with_single_narration(
            title=f'Класіка {i + 1}',
            tags=[tag_classics],
            authors=[person_valer],
            narrators=[person_adam],
        )

def seed_media_dir():
    if os.path.exists(settings.MEDIA_ROOT):
        shutil.rmtree(settings.MEDIA_ROOT)
    shutil.copytree(os.path.join(settings.BASE_DIR, 'seed_media'), settings.MEDIA_ROOT)

def create_superuser():
    User = get_user_model()
    User.objects.create_superuser('admin@example.com', '12345')
    # superuser_pass = os.environ.get('DJANGO_SUPERUSER_PASSWORD', None)
    # assert superuser_pass, 'DJANGO_SUPERUSER_PASSWORD must be set when using --create-superuser option'
    # email = 'admin@example.com'
    # call_command('createsuperuser', '--no-input', email=email)
    print(f'Created superuser admin@example.com with pass 12345')


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
        if os.path.exists(db_path):
            if options['skip_if_exists']:
                print(
                    f'Not creating database {db_path} as it already exists and --skip-if-exists is enabled.'
                )
                return
            else:
                print(f'Dropping database {db_path}')
                os.remove(db_path)
        print(f'Creating database {db_path}')
        call_command('makemigrations')
        call_command('migrate', 'books', 'zero')
        call_command('migrate', 'user', 'zero')
        call_command('migrate')
        fill_with_data()
        seed_media_dir()
        create_superuser()
        print('Completed!')
