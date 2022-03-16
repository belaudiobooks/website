'''
Import audiobooks from Yandex.Music Vyseishaya Shkola collection.
'''
import json
from typing import List
from data_scripts import books
from data_scripts.util import open_url

BASE_URL = 'https://music.yandex.by'
LABEL_URL = f'{BASE_URL}/label/4331524/albums'

ARTISTS_NAMES = {
    'Кухарава Н.': 'Наталля Кухарава',
    'Н. Кухарава': 'Наталля Кухарава',
    'Каляда А.': 'Андрэй Каляда',
}


def _get_books_urls() -> List[str]:
    page = open_url(LABEL_URL)
    links = page.select('.album .album__title a')
    return [BASE_URL + link.attrs['href'] for link in links]


def _maybe_add_book(data: books.BooksData, url: str) -> None:
    page = open_url(url)
    print(f'processing {url}')
    title_parts = page.select_one('.page-album__title').string.split('.')
    for script in page.select('script'):
        if 'var Mu={' in script.text:
            print('found')
            config_json = script.text.removeprefix('var Mu=').removesuffix(';')
            config = json.loads(config_json)
            break
    assert config
    page_data = config['pageData']
    print(page_data['title'])
    title_parts = page_data['title'].split('.')
    title = title_parts[-1].strip()
    if title.startswith('«') and title.endswith('»'):
        title = title[1:-1]

    author = ''
    if len(title_parts) > 1:
        author = title_parts[0]

    print(f'title "{title}"')
    new_title = input('-> ')
    if len(new_title) > 0:
        title = new_title

    print(f'author "{author}"')
    new_author = input('-> ')
    if len(new_author) > 0:
        author = new_author

    narrator = page_data['artists'][0]['name']
    narrator = ARTISTS_NAMES[narrator]
    description = page_data['description']
    duration_sec = 0
    for volume in page_data['volumes']:
        for item in volume:
            duration_sec += item['durationMs'] / 1000

    narration = books.add_or_update_book(data,
                                         title=title,
                                         description=description,
                                         authors=[author],
                                         narrators=[narrator],
                                         translators=[],
                                         cover_url='',
                                         duration_sec=int(duration_sec))
    books.add_or_update_link(narration, 'yandex_podcast', url)


def run(data: books.BooksData) -> None:
    '''Run mains'''
    for url in _get_books_urls():
        _maybe_add_book(data, url)