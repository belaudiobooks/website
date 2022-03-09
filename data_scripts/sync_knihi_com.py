from dataclasses import dataclass
from typing import List
import bs4
import requests
from . import books


def _open_url(url: str) -> bs4.BeautifulSoup:
    resp = requests.get(url)
    resp.encoding = 'utf8'
    if resp.status_code != 200:
        raise ValueError(f'URL {url} returned {resp.status_code}')
    return bs4.BeautifulSoup(resp.text, 'html.parser')


@dataclass
class RawBook:
    '''All book-related data in one object.'''
    title: str
    author: str
    narrator: str
    url: str


def _get_raw_books() -> List[RawBook]:
    list = _open_url('https://knihi.com/audyjoknihi.html').select('ul')[1]
    result = []
    for item in list.children:
        if item.name is None:
            continue
        if item.name == 'div':
            print(item)
            break
        narrator_el = item.select_one('i')
        if narrator_el is None:
            narrator = ''
        else:
            narrator = narrator_el.string.removeprefix('чытае ')
        links = item.select('a')
        links.pop(0)  # remove file link
        author = ''
        if len(links) > 1:
            author = links.pop(0).string
        for link in links:
            title = link.string
            url = link['href']
            result.append(
                RawBook(title=title, author=author, narrator=narrator,
                        url=url))
    print(f'total books {len(result)}')
    return result


def _add_book(data: books.BooksData, idx: int, raw_book: RawBook) -> None:
    print(f'\n\n#{idx + 1}')
    print(raw_book.title)
    print(f'author: {raw_book.author}')
    print(f'narrator: {raw_book.narrator}')
    url = f'https://knihi.com{raw_book.url}'
    print(url)
    print('')
    print('what to do? 1 - skip, 2 - accept, 3 - edit')
    action = None
    while True:
        action = input('-> ')
        if action == '1':
            return
        if action == '2' or action == '3':
            break
        print('wrong')
    if action == '3':
        print(f'title {raw_book.title}')
        new_title = input('-> ')
        if len(new_title) > 0:
            raw_book.title = new_title

        print(f'author "{raw_book.author}"')
        new_author = input('-> ')
        if len(new_author) > 0:
            raw_book.author = new_author

        print(f'narrator "{raw_book.narrator}"')
        new_narrator = input('-> ')
        if len(new_narrator) > 0:
            raw_book.narrator = new_narrator

    narrators = []
    if len(raw_book.narrator) > 0:
        narrators = raw_book.narrator.split(',')
    narration = books.add_or_update_book(data,
                                         title=raw_book.title,
                                         description='',
                                         authors=raw_book.author.split(','),
                                         narrators=narrators,
                                         translators=[],
                                         cover_url='',
                                         duration_sec=0)
    books.add_or_update_link(narration=narration,
                             url_type='knihi_com',
                             url=url)


def run(data: books.BooksData) -> None:
    '''Run mains'''
    start = 140
    step = 10
    for idx, raw_book in enumerate(_get_raw_books()):
        if idx >= start and idx < start + step:
            _add_book(data, idx, raw_book)