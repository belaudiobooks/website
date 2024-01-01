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
from books.models import Book, BookStatus, Narration, Person, Publisher, Tag, Link, LinkType, LinkAvailability, Gender, Language
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
        livelib_url: str = '',
        cover_image: str = '',
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
        cover_image=cover_image,
    )
    narration.narrators.set(narrators)
    narration.translators.set(translators)
    narration.publishers.set(publishers)
    for link_type in link_types:
        narration.links.add(
            Link.objects.create(url=f'http://{link_type.name}.com', url_type=link_type)
        )
    narration.save()
    return book

def fill_with_data():
    tag_proza = Tag.objects.create(name='Сучасная проза', slug='proza')
    tag_classics = Tag.objects.create(name='Класікі беларускай літаратуры', slug='classics')
    tag_children = Tag.objects.create(name='Дзецям і падлеткам', slug='children')

    link_type_kobo = LinkType.objects.create(
        name='kobo',
        caption='Kobo',
        icon='icons/kobo.jpg',
        weight=10,
        availability=LinkAvailability.EVERYWHERE,
    )
    link_type_knizhny_voz = LinkType.objects.create(
        name='knizhny_voz',
        caption='Кніжны Воз',
        icon='icons/knizhny_voz.png',
        weight=9,
        availability=LinkAvailability.EVERYWHERE
    )
    link_type_google_play = LinkType.objects.create(
        name='google_play_books',
        caption='Google Play Books',
        icon='icons/google_play_books.png',
        weight=8,
        availability=LinkAvailability.UNAVAILABLE_IN_BELARUS,
    )
    link_type_spotify_audiobooks = LinkType.objects.create(
        name='spotify_audiobooks',
        caption='Spotify Audiobooks',
        icon='icons/spotify_audiobooks.png',
        weight=7,
        availability=LinkAvailability.USA_ONLY,
    )

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
        date_of_birth='1990-01-01',
        gender=Gender.MALE)
    person_bahdana = Person.objects.create(
        name='Багдана Багданаўна',
        slug='bahdana-bahdanawna',
        description='Біяграфія Багданы Багданаўны тут',
        photo='photos/bahdana.png',
        date_of_birth='1980-02-02',
        gender=Gender.FEMALE)
    person_valer = Person.objects.create(
        name='Валер Валеравіч',
        slug='valer-valeravich',
        date_of_birth='1970-03-03',
        gender=Gender.MALE)

    for i in range(6):
        create_book_with_single_narration(
            title=f'Проза {i + 1}',
            tags=[tag_proza],
            authors=[person_adam],
            narrators=[person_bahdana],
            publishers=[publisher_audiobooksby],
            link_types=[link_type_kobo],
            date=date.today()-timedelta(days=i),
            cover_image=f'covers/proza_{i+1}.png',
        )
        create_book_with_single_narration(
            title=f'Дзіцячая кніга {i + 1}',
            tags=[tag_children],
            authors=[person_bahdana],
            narrators=[person_valer],
            publishers=[publisher_knizhny_voz],
            link_types=[link_type_knizhny_voz],
            date=date.today()-timedelta(days=i),
            cover_image=f'covers/kids_{i+1}.png',
        )
        create_book_with_single_narration(
            title=f'Класіка {i + 1}',
            tags=[tag_classics],
            authors=[person_valer],
            narrators=[person_adam],
            date=date.today()-timedelta(days=i),
            link_types=[link_type_kobo],
        )

    # create book with as much data as possible
    megabook = Book.objects.create(
        title='Мегакніга',
        title_ru=f'Мегакнига по-русски',
        description=f'Кніга ў якой сабраны ўсе магчымыя дадзеныя',
        description_source='Github;https://github.com/belaudiobooks/website',
        status=BookStatus.ACTIVE,
        livelib_url='https://www.livelib.ru/book/1000000000',
        preview_url='https://youtube.com',
    )
    megabook.authors.set([person_adam, person_bahdana, person_valer])
    megabook.tag.set([tag_proza, tag_classics, tag_children])
    megabook_nar_1 = Narration.objects.create(
        language=Language.BELARUSIAN,
        duration=timedelta(hours=1, minutes=15),
        book=megabook,
        paid=True,
        date=date.today()+timedelta(days=1),
        description='Апісанне першай агучкі',
        cover_image='covers/megabook_1.png',
        cover_image_source='ChatGPT;https://chat.openai.com',
    )
    megabook_nar_1.narrators.set([person_adam, person_bahdana, person_valer])
    megabook_nar_1.translators.set([person_adam, person_bahdana, person_valer])
    megabook_nar_1.links.set([
        Link.objects.create(url='http://kobo.com', url_type=link_type_kobo),
        Link.objects.create(url='http://knizhnyvoz.com', url_type=link_type_knizhny_voz),
        Link.objects.create(url='http://google.com', url_type=link_type_google_play),
        Link.objects.create(url='http://spotify.com', url_type=link_type_spotify_audiobooks),
    ])
    megabook_nar_2 = Narration.objects.create(
        language=Language.BELARUSIAN,
        duration=timedelta(hours=2, minutes=15),
        book=megabook,
        paid=False,
        date=date.today(),
        cover_image='covers/megabook_2.png',
    )
    megabook_nar_2.narrators.set([person_adam, person_bahdana, person_valer])
    megabook_nar_2.translators.set([person_adam])
    megabook_nar_2.links.set([
        Link.objects.create(url='http://kobo.com', url_type=link_type_kobo),
        Link.objects.create(url='http://knizhnyvoz.com', url_type=link_type_knizhny_voz),
    ])
    megabook_nar_3 = Narration.objects.create(
        language=Language.RUSSIAN,
        duration=timedelta(hours=3, minutes=15),
        book=megabook,
        paid=False,
        date=date.today(),
    )
    megabook_nar_3.links.set([
        Link.objects.create(url='http://google.com', url_type=link_type_google_play),
        Link.objects.create(url='http://spotify.com', url_type=link_type_spotify_audiobooks),
    ])


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
        call_command('migrate')
        fill_with_data()
        seed_media_dir()
        create_superuser()
        print('Completed!')
