'''
Imports books from soundcloud. For soundcloud we need a link to the playlist.
Import is interactive and it asks for book title, author, narrator as they are not
available from data easily. Soundcloud API is not possible to use as it requires developer
registration but registration is closed right now.
'''

from datetime import datetime
import json
import os
import re
import requests
from . import books, image
from django.core.files import File

RADIO_SVABODA_URLS = [
    'https://soundcloud.com/svaboda/sets/halina-rudnik-ptuski-pieralotnyja',
    'https://soundcloud.com/svaboda/sets/nuu3c9p73ys5',
    'https://soundcloud.com/svaboda/sets/nejynpc52y23',
    'https://soundcloud.com/svaboda/sets/zhyvaya_mova_yuras_bushlyakou_kniha_svaboda',
    'https://soundcloud.com/svaboda/sets/bykau-ddd',
    'https://soundcloud.com/svaboda/sets/ey1dfbhdowb6',
    'https://soundcloud.com/svaboda/sets/tp02qnj10ika',
    'https://soundcloud.com/svaboda/sets/cdncibpherhx',
    'https://soundcloud.com/svaboda/sets/albom_siamejny',
    'https://soundcloud.com/svaboda/sets/kalinouski_sprava_bialiackaha',
    'https://soundcloud.com/svaboda/sets/astravec-1991',
    'https://soundcloud.com/svaboda/sets/dubianecki_memo',
    'https://soundcloud.com/svaboda/sets/sadouski_poshuki',
    'https://soundcloud.com/svaboda/sets/imiony-svabody',
    'https://soundcloud.com/svaboda/sets/ara',
    'https://soundcloud.com/svaboda/sets/padarozza-u-bnr',
    'https://soundcloud.com/svaboda/sets/zaraslava-kaminskaya-kalyadny-stol',
    'https://soundcloud.com/svaboda/sets/oswald-u-miensku',
    'https://soundcloud.com/svaboda/sets/alena-brava-sadomskaya-yablynya',
    'https://soundcloud.com/svaboda/sets/bakharevich-sabaki-europy',
    'https://soundcloud.com/svaboda/sets/vintses-mudrou-zaboytsa-anyola',
    'https://soundcloud.com/svaboda/sets/adam-globus-syamya',
    'https://soundcloud.com/svaboda/sets/uladzimir_arlou-tancy_nad_horadam',
    'https://soundcloud.com/svaboda/sets/bartosik_klinika'
]

MOVA_NANOVA_URLS = [
    'https://soundcloud.com/maxim-umetsky/sets/nu-lya-vy-ya-1',
    'https://soundcloud.com/maxim-umetsky/sets/1ozouubviyjh',
]

PENBELARUS_URLS = [
    'https://soundcloud.com/pencentre_by/sets/uryk-kng-z-karotkaga-spsu-prem-gedroytsya-2021',
    'https://soundcloud.com/pencentre_by/sets/ganna-yankuta-kot-shprot-vezhavy-gadznnk',
]


def _sync_book(data: books.BooksData, url: str, url_type: str) -> None:
    print(f'Processing url {url}. ')
    is_cont = input('Continue? -> ')
    if is_cont != 'y' and is_cont != 'yes':
        return
    resp = requests.get(url)
    resp.encoding = 'utf8'
    if resp.status_code != 200:
        raise ValueError(f'URL returned {resp.status_code}')
    match = re.search('window.__sc_hydration = (.*);</script>', resp.text)
    if match is None:
        raise ValueError('Did not found JSON in html source.')
    json_data = json.loads(match.group(1))
    playlist = None
    for item in json_data:
        if item['hydratable'] == 'playlist':
            playlist = item['data']
    assert playlist is not None, f'Did not found playlist in JSON {json_data}'
    playlist_title = playlist['title']
    print(f'Playlist title is "{playlist_title}"')
    author = ''
    title = ''
    parts = playlist_title.split('.')
    if len(parts) > 1:
        author = parts[0].strip()
        title = parts[1].strip()
    print(f'base title: {title}')
    new_title = input('new title? -> ')
    if new_title != '':
        title = new_title
    print(f'base author: {author}')
    new_author = input('new author? -> ')
    if new_author != '':
        author = new_author
    narrator = input('narrator? -> ')
    if narrator == 'same':
        narrator = author
    translator = input('translator? -> ')
    translators = []
    if len(translator) > 0:
        translators = translator.split(',')
    cover = ''
    if playlist['artwork_url'] is not None:
        cover = playlist['artwork_url'].replace('-large.', '-t500x500.')
    cover_book_or_author = input('cover book or author? -> ')
    narration = books.add_or_update_book(
        data,
        title=title,
        description=playlist['description']
        if playlist['description'] is not None else '',
        authors=author.split(','),
        narrators=narrator.split(','),
        translators=translators,
        cover_url=cover if cover_book_or_author == 'book' else '',
        duration_sec=round(playlist['duration'] / 1000))
    assert narration.book
    author = narration.book.authors.first()
    if cover != '' and cover_book_or_author == 'author' and (
            author.photo is None or author.photo == ''
            or author.photo.name is None):
        cover_image = image.download_and_resize_image(cover, author.slug)
        with open(cover_image, 'rb') as f:
            author.photo.save(os.path.basename(cover_image), File(f))
        author.save()
    narration.book.date = datetime.fromisoformat(
        playlist['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
    books.add_or_update_link(narration, url_type, url)


def run(data: books.BooksData) -> None:
    '''Run mains'''
    # for url in RADIO_SVABODA_URLS:
    #     _sync_book(data, url, 'radio_svaboda')
    # for url in MOVA_NANOVA_URLS:
    #     _sync_book(data, url, 'movananova')
    start = 100
    step = 10
    for idx, url in enumerate(PENBELARUS_URLS):
        if idx >= start and idx < start + step:
            _sync_book(data, url, 'penbelarus')
