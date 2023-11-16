"""
Views that display information about a particular publisher.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404

from books.models import BookStatus, Publisher


def publisher_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Detailed publisher page"""

    publisher = get_object_or_404(Publisher, slug=slug)
    narrations = publisher.narrations.order_by('-date')
    books = [
        item.book for item in narrations
        if item.book.status == BookStatus.ACTIVE
    ]
    context = {
        'publisher': publisher,
        'books': books,
    }
    return render(request, 'books/publisher.html', context)