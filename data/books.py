"""Core utilities and objects for working with data.json file.

Each run script should use this module in the following way:
1. Call read_books_data() to get current BooksData object from data.json.
2. Fetch and parse data from whatever sources it handles (e.g. podcast's feed rss.xml).
3. Call add_or_sync_book() for each book it needs to add/update in the data.
4. Call write_books_data() to update data.json.
"""

from dataclasses import dataclass, asdict
import json
from typing import List
import os
from . import image


@dataclass
class Person:
    """Author/translator/narrator."""
    id: int
    name: str


@dataclass
class Link:
    """Link to a page where user can listen that book."""
    type: str
    url: str


@dataclass
class Book:
    """Book class.

    authors/narrators/translators field are lists of ids.
    """
    id: int
    title: str
    description: str
    authors: List[int]
    narrators: List[int]
    translators: List[int]
    links: List[Link]
    cover_image: str


@dataclass
class LinkType:
    """Type of a link that points to specific audibook platform, e.g. google podcast or LitRes"""
    name: str
    caption: str
    icon_url: str


@dataclass
class BooksData:
    """All book-related data in one object."""
    people: List[Person]
    books: List[Book]
    link_types: List[LinkType]


def _get_or_add_person(data: BooksData, name: str) -> Person:
    max_id = 0
    for person in data.people:
        if person.name == name:
            return person
        max_id = max(max_id, person.id)
    max_id += 1
    person = Person(id=max_id, name=name)
    data.people.append(person)
    return person


def _to_list_of_ids(data: BooksData, people: List[str]) -> List[int]:
    return [_get_or_add_person(data, name).id for name in people]


def _merge_links(book: Book, links: List[Link]) -> None:
    for link in links:
        found = False
        for existing_link in book.links:
            if link.type == existing_link.type:
                existing_link.url = link.url
                found = True
        if not found:
            book.links.append(link)


def add_or_sync_book(data: BooksData, title: str, description: str,
                     authors: List[str], narrators: List[str],
                     translators: List[str], links: List[Link],
                     cover_url: str) -> None:
    """Method for updating BooksData with new data.

    If given book already exists in BooksData (compared by title) -
    the existing book object is updated. Some fields are overriden, some are
    merged. If the book doesn't exist - a new books is created with provided fields."""
    max_id = 0
    book = None
    for existing_book in data.books:
        if existing_book.title.lower() == title.lower():
            book = existing_book
            break
        max_id = max(max_id, existing_book.id)
    if book is None:
        cover_image = image.download_and_resize_image(cover_url,
                                                      _translit(title))
        book = Book(id=max_id + 1,
                    title=title,
                    description=description,
                    authors=[],
                    translators=[],
                    narrators=[],
                    links=[],
                    cover_image=cover_image)
        data.books.append(book)
    book.authors = _to_list_of_ids(data, authors)
    book.narrators = _to_list_of_ids(data, narrators)
    book.translators = _to_list_of_ids(data, translators)
    for link in links:
        if link.url is None:
            raise ValueError(
                f"Got null url for book {title} link type {link.type}")
    if description != "":
        book.description = description
    _merge_links(book, links)


DATA_FILE = os.path.dirname(os.path.realpath(__file__)) + '/data.json'


def read_books_data(file: str = DATA_FILE) -> BooksData:
    """Read all data from data.json file."""
    with open(file, "r", encoding="utf8") as f:
        data = json.loads(f.read())
        people = [Person(**person) for person in data["people"]]
        books = []
        for json_book in data["books"]:
            json_book["links"] = [
                Link(link["type"], link["url"]) for link in json_book["links"]
            ]
            books.append(Book(**json_book))
        link_types = [LinkType(**link) for link in data["link_types"]]
        return BooksData(people, books, link_types)


def write_books_data(data: BooksData, file: str = DATA_FILE) -> None:
    """Write given BooksData to the data.json."""
    with open(file, "w", encoding="utf8") as f:
        json.dump(asdict(data), f, ensure_ascii=False, indent=2)


CYRILLIC = 'а,б,в,г,д,е,ё,ж,з,и,й,к,л,м,н,о,п,р,с,т,у,ф,х,ц,ч,ш,щ,ъ,ы,ь,э,ю,я,і,ў'.split(
    ",")
LATIN = 'a,b,v,g,d,e,jo,zh,z,i,j,k,l,m,n,o,p,r,s,t,u,f,h,c,ch,sh,shh,,y,,je,ju,ja,i,u'.split(
    ",")
CYRILLIC_TO_LATIN = dict(zip(CYRILLIC, LATIN))


def _translit(sentence: str) -> str:
    res = ""
    for char in sentence.lower():
        if char in CYRILLIC_TO_LATIN:
            res += CYRILLIC_TO_LATIN[char]
        elif char == " ":
            res += "_"
        elif char.isalnum():
            res += char
    return res
