"""
Views that display information about a particular person.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, query

from books.models import Person, Narration, Book

from .utils import maybe_filter_links, BookForPreview


def get_active_books(books: query.QuerySet, request: HttpRequest) -> query.QuerySet:
    # order narrations by date so that the newest one last so that we can render
    # cover stack correctly with the latest bein on top.
    narrations_by_date = Prefetch(
        "narrations", queryset=Narration.objects.order_by("date")
    )
    active_books = books.prefetch_related(narrations_by_date)
    return maybe_filter_links(active_books, request).distinct()


def person_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Detailed book page"""

    # Prefetch all books in the relationships
    person = get_object_or_404(
        Person.objects.prefetch_related(
            "books_authored", "narrations", "narrations_translated"
        ),
        slug=slug,
    )

    narration_ids = person.narrations.values_list("uuid", flat=True)
    narrated_books = Book.objects.active_books_ordered_by_date().filter(
        narrations__uuid__in=narration_ids
    )
    narrated_books = get_active_books(narrated_books, request)

    narrations_translated_ids = person.narrations_translated.values_list(
        "uuid", flat=True
    )
    translated_books = Book.objects.active_books_ordered_by_date().filter(
        narrations__uuid__in=narrations_translated_ids
    )
    translated_books = get_active_books(translated_books, request)

    authored_books = Book.objects.active_books_ordered_by_date().filter(
        authors__uuid=person.uuid
    )
    authored_books = get_active_books(authored_books, request)

    context = {
        "person": person,
        "authored_books": [
            BookForPreview.with_all_narrations(book) for book in authored_books
        ],
        "translated_books": [
            BookForPreview.with_narrations_from_translator(book, person)
            for book in translated_books
        ],
        "narrated_books": [
            BookForPreview.with_narrations_from_narrator(book, person)
            for book in narrated_books
        ],
    }

    return render(request, "books/person.html", context)
