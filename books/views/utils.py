'''
Utility functions and constants used by multiple views.
'''

from dataclasses import dataclass
from collections.abc import Sequence
from django.db.models import query
from django.http import HttpRequest

from books import models

@dataclass
class BookForPreview:
    """Class containing necessary information to render a book preview."""
    book: models.Book
    narrations: Sequence[models.Narration]

    def __post_init__(self):
        self.narrations = sorted(self.narrations, key=lambda n: n.date)

    @staticmethod
    def with_all_narrations(book: models.Book) -> 'BookForPreview':
        return BookForPreview(book, book.narrations.all())

    @staticmethod
    def with_latest_narration(book: models.Book) -> 'BookForPreview':
        preview = BookForPreview(book, book.narrations.all())
        return BookForPreview(book, preview.narrations[-1:])

    @staticmethod
    def with_narrations_from_narrator(book: models.Book, narrator: models.Person) -> 'BookForPreview':
        narrations = book.narrations.filter(narrators__in=[narrator])
        return BookForPreview(book, narrations)

    @staticmethod
    def with_narrations_from_translator(book: models.Book, translator: models.Person) -> 'BookForPreview':
        narrations = book.narrations.filter(translators__in=[translator])
        return BookForPreview(book, narrations)

def maybe_filter_links(books_query: query.QuerySet,
                       request: HttpRequest) -> query.QuerySet:
    '''
    Filters given Book query set to keep only the books that have at least one
    link of type passed as `links` url param. For example /catalog?links=knihi_com
    should show only books that hosted on knihi.com.
    '''
    links = request.GET.get('links')
    if links is None:
        return books_query
    return books_query.filter(
        narrations__links__url_type__name__in=links.split(','))
