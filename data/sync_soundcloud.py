'''
Imports books from soundcloud. For soundcloud we need a link to the playlist.
Import is interactive and it asks for book title, author, narrator as they are not
available from data easily. Soundcloud API is not possible to use as it requires developer
registration but registration is closed right now.
'''

from datetime import datetime
import json
import re
import requests
from data import books

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


def _sync_book(data: books.BooksData, url: str, url_type: str) -> None:
    print(f'Processing url {url}')
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
    title = input('book title? -> ')
    while title not in playlist_title:
        title = input('title is not found in title, again -> ')
    author = input('author? -> ')
    while author == '':
        author = input('author cannot be empty, again -> ')
    narrator = input('narrator? -> ')
    if narrator == '' or narrator is None:
        narrator = author
    cover = playlist['artwork_url'].replace('-large.', '-t500x500.')
    narration = books.add_or_update_book(
        data,
        title=title,
        description=playlist['description']
        if playlist['description'] is not None else '',
        authors=author.split(','),
        narrators=narrator.split(','),
        translators=[],
        cover_url=cover,
        duration_sec=round(playlist['duration'] / 1000))
    assert narration.book
    narration.book.date = datetime.fromisoformat(
        playlist['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
    books.add_or_update_link(narration, url_type, url)


def run(data: books.BooksData) -> None:
    '''Run mains'''
    # for url in RADIO_SVABODA_URLS:
    #     _sync_book(data, url, 'radio_svaboda')
    for url in MOVA_NANOVA_URLS:
        _sync_book(data, url, 'movananova')
