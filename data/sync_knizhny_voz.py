'''Syncer that loads data from https://knizhnyvoz.by/books/'''

from typing import Any, List, Dict, Set
import requests
from . import books

DATA_URL = 'https://knizhnyvoz.by/books/'


def _clean_title(title: str) -> str:
    return title.strip()


def _clean_description(description: str) -> str:
    return description.strip()


# Most names have form 'FirstName LastName' but in few cases
# on their site it is 'LastName FirstName'. To handle those -
# we harcode those first names so that they can swapped.
FIRST_NAMES = {
    'Крысціна',
    'Зміцер',
    'Сяргей',
}

# Some names contain prefixes/suffixes which we don't need.
NON_NAME_PARTS = {
    ', Свабодны Купалавец',
    'Народная артыстка Беларусі',
    'актор',
    'актрыса',
    'Народны артыст Беларусі',
    # Don't need patronymic name either.
    'Андрэевіч',
}


def _clean_name(raw_name: str) -> List[str]:
    raw_name = raw_name.strip()
    # Often names end with a double quote for some reason. Remove it.
    if raw_name.count('"') == 1:
        raw_name = raw_name.replace('"', '')
    names = [raw_name]
    # Handle specific case.
    if raw_name == 'Юя і Томас Вісландэры':
        names = ['Юя Вісландэр', 'Томас Вісландэр']
    # Handle cases like 'Іван Іваноў і Мікола Мікалаеў'.
    elif ' і ' in raw_name:
        names = raw_name.split(' і ')
    clean_names = []
    for name in names:
        for to_remove in NON_NAME_PARTS:
            name = name.replace(to_remove, '').strip().replace('  ', ' ')
        parts = name.split(' ')

        # See comment on FIRST_NAMES.
        if len(parts) == 2 and parts[1] in FIRST_NAMES:
            name = parts[1] + ' ' + parts[0]
        clean_names.append(name)
    return clean_names


def _get_duration_sec(id: str) -> int:
    chapters: List[Dict] = requests.get(
        'https://knizhnyvoz.herokuapp.com/books/' + id).json()
    duration_ms = 0
    for chapter in chapters:
        duration_ms += chapter['duration']
    return int(duration_ms / 1000)


def add_or_sync_book_voz(data: books.BooksData, book: dict[str, Any]) -> None:
    '''
    Given a book object from knizhnyvoz JSON - picks and cleans necessary
    parts and adds it to BooksData. To understand that method better check
    format in https://knizhnyvoz.by/books/
    '''
    title = _clean_title(book['name'])
    print(f'processing {title}')
    roles: Dict[str, List[str]] = {}
    for role in book['roles']:
        names = []
        for raw_name in role['names']:
            for name in _clean_name(raw_name):
                names.append(name)
        roles[role['role'].lower()] = names
    authors = roles.get('аўтар', _clean_name(book['author']))
    translators: List[str] = []
    narrators: Set[str] = set()
    for role, names in roles.items():
        if 'пераклад' in role:
            translators = names
        elif 'чытае' in role or 'чытаюць' in role or 'выконвае' in role:
            narrators = {*narrators, *names}

    narrators_list = list(narrators)
    narrators_list.sort()
    db_book = books.add_or_update_book(
        data,
        title=title,
        description=_clean_description(book['description']),
        authors=authors,
        narrators=narrators_list,
        translators=translators,
        cover_url=book['imageUri'],
        duration_sec=_get_duration_sec(book['id']))
    books.add_or_update_link(book=db_book,
                             url_type='knizhny_voz',
                             url='https://knizhnyvoz.by/app/book/' +
                             book['id'])


def run(data: books.BooksData):
    'Synchronizes data.json with data from http://knizhnyvoz.by'
    resp = requests.get(DATA_URL)
    if resp.status_code != 200:
        raise ValueError(f'URL {DATA_URL} returned {resp.status_code}')
    data_json: list[dict[str, Any]] = resp.json()
    for book_json in data_json:
        add_or_sync_book_voz(data, book_json)
