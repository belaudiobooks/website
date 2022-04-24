import logging
from typing import Dict, List, Union
from django import views
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.core.management import call_command
from django.urls import reverse
from django.db.models import query
from algoliasearch.search_client import SearchClient

from .models import Book, BookStatus, Person, Tag

active_books = Book.objects.filter(
    status=BookStatus.ACTIVE).prefetch_related('authors')

logger = logging.getLogger(__name__)

TAGS_TO_SHOW_ON_MAIN_PAGE = [
    'Сучасная проза',
    'Класікі беларускай літаратуры',
    'Дзецям і падлеткам',
]

BOOKS_PER_PAGE = 16


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


def index(request: HttpRequest) -> HttpResponse:
    '''Index page, starting page'''
    # Getting all Tags and creating querystring objects for each to pass to template
    tags_to_render = []
    for tag in Tag.objects.filter(name__in=TAGS_TO_SHOW_ON_MAIN_PAGE):
        tags_to_render.append({
            'name':
            tag.name,
            'slug':
            tag.slug,
            'books':
            active_books.filter(tag=tag.id).order_by('-added_at'),
        })

    context = {
        'promo_books': active_books.filter(promoted=True),
        'recently_added_books': active_books.order_by('-added_at')[:6],
        'tags_to_render': tags_to_render,
    }

    return render(request, 'books/index.html', context)


def catalog(request: HttpRequest, slug: str = '') -> HttpResponse:
    '''Catalog page for specific tag or all books'''

    page = request.GET.get('page')
    tags = Tag.objects.all()
    filtered_books = maybe_filter_links(active_books, request)
    links_filter = ''
    if request.GET.get('links'):
        links_filter = '&links=' + request.GET.get('links')

    if slug:
        #get selected tag id
        tag = tags.filter(slug=slug).first()
        #pagination for the books by tag
        books_by_tag = filtered_books.filter(tag=tag.id).order_by('-added_at')
        paginator_by_tag = Paginator(books_by_tag, BOOKS_PER_PAGE)
        page_by_tag = request.GET.get('page')
        paged_books_by_tag = paginator_by_tag.get_page(page_by_tag)

        context = {
            'all_books': paged_books_by_tag,
            'selected_tag': tag,
            'tags': tags,
            'links_filter': links_filter,
        }
    else:
        sorted_books = filtered_books.order_by('-added_at')
        paginator = Paginator(sorted_books, BOOKS_PER_PAGE)
        paged_books = paginator.get_page(page)
        context = {
            'all_books': paged_books,
            'tags': tags,
            'links_filter': links_filter,
        }

    return render(request, 'books/all-books.html', context)


def book_detail(request: HttpRequest, slug: str) -> HttpResponse:
    '''Detailed book page'''
    identified_book = get_object_or_404(Book, slug=slug)

    context = {
        'book': identified_book,
        'authors': identified_book.authors.all(),
        'translators': identified_book.translators.all(),
        'narrations': identified_book.narrations.all(),
        'tags': identified_book.tag.all(),
    }

    return render(request, 'books/book-detail.html', context)


def person_detail(request: HttpRequest, slug: str) -> HttpResponse:
    '''Detailed book page'''

    # TODO: remove it later if all good
    # identified_person = get_object_or_404(Person, slug=slug)

    # Prefetch all books in the relationships
    person = Person.objects.prefetch_related(
        'books_authored', 'books_translated',
        'narrations').filter(slug=slug).first()

    if person:
        author = maybe_filter_links(
            person.books_authored.all().filter(status=BookStatus.ACTIVE),
            request)
        translator = maybe_filter_links(
            person.books_translated.all().filter(status=BookStatus.ACTIVE),
            request)
        narrations = person.narrations.all().filter()
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


def search(request: HttpRequest) -> HttpResponse:
    '''Search results'''
    query = request.GET.get('query')

    if query:
        client = SearchClient.create(settings.ALGOLIA_APPLICATION_ID,
                                     settings.ALGOLIA_SEARCH_KEY)
        index = client.init_index(settings.ALGOLIA_INDEX)
        # Response:
        # ttps://www.algolia.com/doc/guides/building-search-ui/going-further/backend-search/in-depth/understanding-the-api-response/
        hits = index.search(query, {'hitsPerPage': 100})['hits']

        # Load all models, books and people returned from algolia.
        people_ids: List[str] = []
        books_ids: List[str] = []
        for hit in hits:
            if hit['model'] == 'person':
                people_ids.append(hit['objectID'])
            elif hit['model'] == 'book':
                books_ids.append(hit['objectID'])
            else:
                logger.warning('Got unexpected model from search %s',
                               hit['model'],
                               extra=hit)
        loaded_models: Dict[str, Union[Person, Book]] = {}
        for person in Person.objects.all().filter(uuid__in=people_ids):
            loaded_models[str(person.uuid)] = person
        for book in Book.objects.all().prefetch_related('authors').filter(
                uuid__in=books_ids):
            loaded_models[str(book.uuid)] = book

        # Build search result list in the same order as returned by algolia.
        # So that most relevant are shown first.
        search_results = [{
            'type': hit['model'],
            'object': loaded_models[hit['objectID']]
        } for hit in hits]

        context = {
            'results': search_results[:50],
            'query': query,
        }

    else:
        context = {
            'results': [],
            'query': '',
        }

    return render(request, 'books/search.html', context)


def about(request: HttpRequest) -> HttpResponse:
    '''About us page containing info about the website and the team.'''
    people = [
        ('Мікіта', 'images/member-mikita.jpg'),
        ('Яўген', 'images/member-jauhen.jpg'),
        ('Павал', 'images/member-paval.jpg'),
        ('Алесь', 'images/member-ales.jpg'),
        ('Наста', 'images/member-nasta.jpg'),
        ('Алёна', 'images/member-alena.jpg'),
        ('Юры', 'images/member-jura.jpg'),
        ('Андрэй', 'images/member-andrey.jpg'),
    ]
    context = {
        'team_members': people,
        'books_count': Book.objects.count(),
    }
    return render(request, 'books/about.html', context)


def push_data_to_algolia(request: HttpRequest) -> HttpResponse:
    '''
    HTTP hook that pushes all data from DB to algolia.
    It's called hourly by an appengine job.
    '''
    call_command('push_data_to_algolia')
    return HttpResponse(status=204)


def page_not_found(request: HttpRequest):
    '''Helper method to test 404 page rendering locally, where using real 404 shows stack trace.'''
    return views.defaults.page_not_found(request, None)


def robots_txt(request: HttpRequest):
    '''
    Serve robots.txt
    https://developers.google.com/search/docs/advanced/robots/intro?hl=en
    '''
    context = {
        'host': request.get_host(),
        'protocol': 'https' if request.is_secure() else 'http'
    }
    return render(request, 'robots.txt', context)


def sitemap(request: HttpRequest):
    '''
    Serve sitemap in text format.
    https://developers.google.com/search/docs/advanced/sitemaps/overview?hl=en
    '''
    pages: List[str] = ['/', '/about', '/catalog']
    for book in active_books:
        pages.append(reverse('book-detail-page', args=(book.slug, )))
    for person in Person.objects.all():
        pages.append(reverse('person-detail-page', args=(person.slug, )))
    for tag in Tag.objects.all():
        pages.append(reverse('catalog-for-tag', args=(tag.slug, )))
    domain = 'https' if request.is_secure() else 'http'
    domain = domain + '://' + request.get_host()
    result = '\n'.join(domain + page for page in pages)
    return HttpResponse(result, content_type='text/plain')
