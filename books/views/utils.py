'''
Utility functions and constants used by multiple views.
'''

from django.db.models import query
from django.http import HttpRequest

from books.models import Book, BookStatus


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


def active_books() -> query.QuerySet:
    '''Returns list of books that are active and should be visible to users.'''
    return Book.objects.filter(
        status=BookStatus.ACTIVE).prefetch_related('authors')
