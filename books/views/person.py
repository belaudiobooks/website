'''
Views that display information about a particular person.
'''

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, query

from books.models import BookStatus, Person, Narration, Book

from .utils import maybe_filter_links


def get_active_books(books: query.QuerySet,
                     request: HttpRequest) -> query.QuerySet:
    narrations_by_date = Prefetch('narrations',
                                  queryset=Narration.objects.order_by('date'))
    active_books = books.order_by('-date').prefetch_related(
        narrations_by_date).filter(status=BookStatus.ACTIVE)
    return maybe_filter_links(active_books, request).distinct()


def person_detail(request: HttpRequest, slug: str) -> HttpResponse:
    '''Detailed book page'''

    # Prefetch all books in the relationships
    person = get_object_or_404(
        Person.objects.prefetch_related('books_authored', 'books_translated',
                                        'narrations'),
        slug=slug,
    )

    narration_ids = person.narrations.values_list('uuid', flat=True)
    narrated_books = Book.objects.filter(narrations__uuid__in=narration_ids)

    narrations_translated_ids = person.narrations_translated.values_list('uuid', flat=True)
    translated_books_ids = Book.objects.filter(
        narrations__uuid__in=narrations_translated_ids).values_list('uuid', flat=True)
    translated_books_ids = translated_books_ids.union(
        person.books_translated.values_list('uuid', flat=True))
    translated_books = get_active_books(
        Book.objects.filter(uuid__in=translated_books_ids), request)

    context = {
        'person': person,
        'authored_books': get_active_books(person.books_authored, request),
        'translated_books': translated_books,
        'narrated_books': get_active_books(narrated_books, request),
    }

    return render(request, 'books/person.html', context)
