'''
Syncer that updates data from ЛитРес store. Additionally it looks up books urls in MyBook service,
which is also owned by LitRes but a different site/catalogue.

By default syncer finds all belarusian audiobooks on LitRes but also has ability to specify
extra books which aren't included in search results.
'''

import datetime
import re
from typing import List, Optional
import requests
import bs4
from data import books

# Dictionary that helps to fix some errors on LitRes data.
REPLACEMENTS = {
    'Дзень Святого Патрыка': 'Дзень Святога Патрыка',
    'Владимир Лисовский': 'Уладзімір Лісоўскі',
    'Ольгерд Бахаревич': 'Альгерд Бахарэвіч',
}


def _maybe_replace(string: str) -> str:
    return REPLACEMENTS.get(string, string)


def _find_mybook_url_by_title(title: str) -> Optional[str]:
    resp = requests.get('https://mybook.ru/search/audiobooks', {'q': title})
    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    for link in soup.select('a'):
        if link.attrs.get('href', '').startswith('/author/'):
            return 'https://mybook.ru' + link['href']
    print(f'Did not found url for bool {title}')
    return None


LITRES_DURATION_FORMAT = re.compile(
    r'(?P<hours>\d+?) ч. (?P<minutes>\d+?) мин. (?P<seconds>\d+?) сек.')


def _sync_book(data: books.BooksData, url: str) -> None:
    resp = requests.get(url)
    if resp.status_code != 200:
        raise ValueError(f'URL {url} returned {resp.status_code}')
    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    orig_title = soup.select_one('.biblio_book_name h1').string
    title = _maybe_replace(orig_title)
    print(f'Processing {title}')
    author = _maybe_replace(
        soup.select_one('.biblio_book_author span[itemprop=name]').string)
    narrator = None
    details = soup.select('.biblio_book_info_detailed li')
    duration = datetime.timedelta()
    for detail in details:
        detail_name = detail.select_one('strong')
        name = '' if detail_name is None else detail_name.string
        if name == 'Чтец:':
            narrator = _maybe_replace(
                detail.select_one('.biblio_info_detailed__link').string)
        elif name == 'Длительность:':
            detail_name.string = ''
            duration_str = '\n'.join(detail.stripped_strings)
            parts = LITRES_DURATION_FORMAT.match(duration_str)
            assert parts, f'Duration regex did not match. {duration_str}'
            time_parts = {}
            for name, param in parts.groupdict().items():
                time_parts[name] = int(param)
            duration = datetime.timedelta(**time_parts)
    assert narrator, 'Did not find narrator'
    description = '\n'.join(
        soup.select_one('.biblio_book_descr_publishers').stripped_strings)
    cover = soup.select_one(
        '.biblio-book-cover-wrapper img')['data-src'].replace(
            '/cover/', '/cover_415/')
    book_model = books.add_or_update_book(data,
                                          title=title,
                                          description=description,
                                          authors=[author],
                                          narrators=[narrator],
                                          translators=[],
                                          cover_url=cover,
                                          duration_sec=int(
                                              duration.total_seconds()))
    books.add_or_update_link(book_model, 'litres', url)
    mybook_url = _find_mybook_url_by_title(orig_title)
    if mybook_url is not None:
        books.add_or_update_link(book_model, 'mybook', mybook_url)


EXTRA_BOOKS = [
    'https://www.litres.ru/maksim-zhbankou/slomo-hatnyaya-krytyka-kulturnaga-dyzaynu-66596742/',
    'https://www.litres.ru/eva-vezhnavec/shlyah-drobnay-svolachy-67123155/',
]


def _get_belarusian_audiobooks_links() -> List[str]:
    search_url = 'https://www.litres.ru/novie/audioknigi/?lang=4'
    resp = requests.get(search_url)
    if resp.status_code != 200:
        raise ValueError(f'URL {search_url} returned {resp.status_code}')
    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    return [
        'https://www.litres.ru' + a['href']
        for a in soup.select('.books_box .cover-image-wrapper a')
    ]


def run(data: books.BooksData):
    '''Sync function. See module description for details.'''
    urls = _get_belarusian_audiobooks_links() + EXTRA_BOOKS
    for url in urls:
        _sync_book(data, url)
