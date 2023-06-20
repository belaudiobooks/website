'''
Views that display information about a particular book.
'''

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404

from books.models import Book, Language

def book_detail(request: HttpRequest, slug: str) -> HttpResponse:
    '''Detailed book page'''
    book = get_object_or_404(Book, slug=slug)

    # Determine if all narrations for the given book are of the same
    # language. That determine whether we show language once at the top
    # or separately for each narration.
    single_language = None
    narrations = book.narrations.all()
    if len(narrations) > 0:
        single_language = narrations[0].language
        for narration in narrations:
            if narration.language != single_language:
                single_language = None
                break

    context = {
        'book': book,
        'authors': book.authors.all(),
        'translators': book.translators.all(),
        'narrations': book.narrations.all(),
        'tags': book.tag.all(),
        'single_language': single_language,
        'show_russian_title': single_language == Language.RUSSIAN,
    }

    return render(request, 'books/book-detail.html', context)
