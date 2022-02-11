from dataclasses import dataclass
from typing import List, Tuple
import bs4
import requests
from data import books


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
    url: str


def _get_raw_books(start: int) -> List[RawBook]:
    result = []
    print(f'processing {start}')
    items = _open_url(
        f'https://kamunikat.org/audyjoknihi.html?pub_start={start}').select(
            '.PubItemContainer')[1:]
    for item in items:
        title = item.select_one('h1 a').string
        url = item.select_one('h1 a')['href']
        author = []
        if len(item.select('h3')):
            author_parts = item.select('h3')[-1].string.split(' ')
            author_parts.reverse()
            author = ' '.join(author_parts)
        book = RawBook(title=title, author=author, url=url)
        result.append(book)
    print(f'total books {len(result)}')
    return result


def _get_description_and_photo(url: str) -> Tuple[str, str]:
    page = _open_url(url)
    description = ''
    if page.select_one('.VolumeSummary p') is not None:
        description = page.select_one('.VolumeSummary p').string
    if description is None:
        description = ''
    img_tag = page.select_one('.PubImageContainer a')
    cover_url = ''
    if img_tag is not None:
        path = img_tag['href']
        cover_url = f'https://kamunikat.org/{path}'
    return (description, cover_url)


def _add_book(data: books.BooksData, idx: int, raw_book: RawBook) -> None:
    print(f'\n\n#{idx + 1}')
    print(raw_book.title)
    print(f'author: {raw_book.author}')
    url = f'https://kamunikat.org{raw_book.url}'
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
    description, cover_url = _get_description_and_photo(url)
    print(description)
    print(cover_url)
    narration = books.add_or_update_book(data,
                                         title=raw_book.title,
                                         description=description,
                                         authors=raw_book.author.split(','),
                                         narrators=[],
                                         translators=[],
                                         cover_url=cover_url,
                                         duration_sec=0)
    books.add_or_update_link(narration=narration,
                             url_type='kamunikat',
                             url=url)


def run(data: books.BooksData) -> None:
    '''Run mains'''
    start = 50
    offset = 0
    step = 10
    for idx, raw_book in enumerate(_get_raw_books(start)):
        if idx >= offset and idx < offset + step:
            _add_book(data, idx, raw_book)