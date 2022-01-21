'''Core utilities and objects for working with data.json file.

Each run script should use this module in the following way:
1. Call read_books_data() to get current BooksData object from data.json.
2. Fetch and parse data from whatever sources it handles (e.g. podcast's feed rss.xml).
3. Call add_or_sync_book() for each book it needs to add/update in the data.
4. Call write_books_data() to update data.json.
'''

from dataclasses import dataclass
import os
from typing import List
from datetime import date
from unidecode import unidecode
from django.template import defaultfilters
from django.core.files import File
from books.models import Book, Person, Link, LinkType
from . import image


@dataclass
class BooksData:
    '''All book-related data in one object.'''
    people: List[Person]
    books: List[Book]


def _slugify(text):
    return defaultfilters.slugify(unidecode(text))


def _get_or_add_person(data: BooksData, name: str) -> Person:
    for person in data.people:
        if person.name == name:
            return person
    person = Person(name=name)
    person.save()
    data.people.append(person)
    return person


def _get_or_create_people(data: BooksData, people: List[str]) -> List[Person]:
    return [_get_or_add_person(data, name) for name in people]


def add_or_update_link(book: Book, url_type: str, url: str) -> None:
    link_type = LinkType.objects.filter(name=url_type).first()
    existing_link = Link.objects.filter(url_type=link_type, book=book)
    if existing_link.count() == 0:
        link = Link(book=book, url_type=link_type, url=url)
        link.save()
    else:
        link = existing_link[0]
        link.url = url
        link.save()


def add_or_update_book(data: BooksData, title: str, description: str,
                       authors: List[str], narrators: List[str],
                       translators: List[str], cover_url: str) -> Book:
    '''Method for updating BooksData with new data.

    If given book already exists in BooksData (compared by title) -
    the existing book object is updated. Some fields are overriden, some are
    merged. If the book doesn't exist - a new books is created with provided fields.'''
    book = None
    authors_full = _get_or_create_people(data, authors)
    for existing_book in data.books:
        title_a = existing_book.title.lower()
        title_b = title.lower()
        # Try handling cases where some books might have shorten names and different
        # sources have different variations of those names.
        if title_a.startswith(title_b) or title_b.startswith(title_a):
            if authors_full[0] != existing_book.authors.all().first():
                print(
                    f'Books "{existing_book.title}" and "{title}" look similar but '
                    + 'have different authors. Not merging.')
            else:
                book = existing_book
                break
    if book is None:
        book = Book(title=title, description=description, date=date.today())
        book.save()
        if len(cover_url):
            cover_image = image.download_and_resize_image(cover_url, book.slug)
            with open(cover_image, 'rb') as f:
                book.cover_image.save(os.path.basename(cover_image), File(f))
            book.save()
        data.books.append(book)
    book.authors.set(authors_full)
    if len(narrators):
        book.narrators.set(_get_or_create_people(data, narrators))
    if len(translators):
        book.translators.set(_get_or_create_people(data, translators))
    if description != '':
        book.description = description
    book.save()
    return book
