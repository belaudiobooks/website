'''
Views that display information about a particular person.
'''

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from books.models import BookStatus, Person

from .utils import maybe_filter_links


def person_detail(request: HttpRequest, slug: str) -> HttpResponse:
    '''Detailed book page'''

    # Prefetch all books in the relationships
    person = Person.objects.prefetch_related(
        'books_authored', 'books_translated',
        'narrations').filter(slug=slug).first()

    if person:
        author = maybe_filter_links(
            person.books_authored.order_by('-date').filter(
                status=BookStatus.ACTIVE), request)
        translator = maybe_filter_links(
            person.books_translated.order_by('-date').filter(
                status=BookStatus.ACTIVE), request)
        narrations = person.narrations.order_by('-book__date').filter()
        if request.GET.get('links'):
            links = request.GET.get('links').split(',')
            narrations = narrations.filter(links__url_type__name__in=links)

        narrated_books = [
            item.book for item in narrations
            if item.book.status == BookStatus.ACTIVE
        ]

        context = {
            'person': person,
            'author': author,
            'translator': translator,
            'narrations': narrated_books,
        }

        return render(request, 'books/person.html', context)

    else:
        pass  #TODO: implement 404 page
