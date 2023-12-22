'''
Views that display information about a particular book.
'''

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Count

from books.models import Book, Language


def book_detail(request: HttpRequest, slug: str) -> HttpResponse:
    '''Detailed book page'''
    book = get_object_or_404(Book, slug=slug)

    # Determine if all narrations for the given book are of the same
    # language. That determine whether we show language once at the top
    # or separately for each narration.
    single_language = None
    # Order narrations - first Belarusian then Russian. Within each
    # language show newer narrations first.
    narrations = book.narrations.order_by('language', '-date').all()
    if len(narrations) > 0:
        single_language = narrations[0].language
        for narration in narrations:
            if narration.language != single_language:
                single_language = None
                break

    context = {
        'book': book,
        'narrations': narrations,
        'tags': book.tag.all(),
        'single_language': single_language,
        'show_russian_title': single_language == Language.RUSSIAN,
        'single_narration': len(narrations) == 1,
    }

    return render(request, 'books/book-detail.html', context)
