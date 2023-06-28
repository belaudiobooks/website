"""
Views that display information about a particular publisher.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from books.models import BookStatus, Publisher


def publisher_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Detailed publisher page"""

    publisher = Publisher.objects.filter(slug=slug).prefetch_related('narrations').first()

    if publisher:
        narrations = publisher.narrations.all().filter()
        narrated_books = [
            item.book for item in narrations
            if item.book.status == BookStatus.ACTIVE
        ]

        context = {
            'publisher': publisher,
            'narrations': narrated_books,
        }

        return render(request, 'books/publisher.html', context)

    else:
        pass  # TODO: implement 404 page
