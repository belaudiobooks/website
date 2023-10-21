'''
Views that are not visible to user. It can be API methods or webmaster
methods such as sitemap or robots.txt.
'''

import json
import logging
from typing import Dict, List, Union
from uuid import UUID
from django import views
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.urls import reverse
from algoliasearch.search_client import SearchClient
from markdownify.templatetags.markdownify import markdownify
from books.thirdparty.livelibru import search_books_with_reviews, DataclassJSONEncoder

from books import serializers, image_cache
from books.models import Book, LinkType, Person, Tag, Publisher

from .utils import active_books
from .articles import ARTICLES

logger = logging.getLogger(__name__)


def search(request: HttpRequest) -> HttpResponse:
    '''Search results'''
    query = request.GET.get('query')

    if query:
        client = SearchClient.create(settings.ALGOLIA_APPLICATION_ID,
                                     settings.ALGOLIA_SEARCH_KEY)
        index = client.init_index(settings.ALGOLIA_INDEX)
        # Response:
        # https://www.algolia.com/doc/guides/building-search-ui/going-further/backend-search/in-depth/understanding-the-api-response/
        hits = index.search(query, {'hitsPerPage': 100})['hits']

        # Load all models, books and people returned from algolia.
        people_ids: List[str] = []
        books_ids: List[str] = []
        publishers_ids: List[str] = []
        for hit in hits:
            if hit['model'] == 'person':
                people_ids.append(hit['objectID'])
            elif hit['model'] == 'book':
                books_ids.append(hit['objectID'])
            elif hit['model'] == 'publisher':
                publishers_ids.append(hit['objectID'])
            else:
                logger.warning('Got unexpected model from search %s',
                               hit['model'],
                               extra=hit)
        loaded_models: Dict[str, Union[Person, Book, Publisher]] = {}
        for person in Person.objects.all().filter(uuid__in=people_ids):
            loaded_models[str(person.uuid)] = person
        for book in Book.objects.all().prefetch_related('authors').filter(
                uuid__in=books_ids):
            loaded_models[str(book.uuid)] = book
        for publisher in Publisher.objects.all().filter(
                uuid__in=publishers_ids):
            loaded_models[str(publisher.uuid)] = publisher
            for book in set(
                [narration.book for narration in publisher.narrations.all()]):
                loaded_models[str(book.uuid)] = book

        def _gettype(value):
            if isinstance(value, Person):
                return 'person'
            elif isinstance(value, Book):
                return 'book'
            elif isinstance(value, Publisher):
                return 'publisher'
            else:
                return 'unknown_type'

        # Build search result list in the same order as returned by algolia.
        # So that most relevant are shown first.
        search_results = [{
            'type': hit['model'],
            'object': loaded_models.pop(hit['objectID'])
        } for hit in hits]

        search_results.extend([{
            'type': _gettype(lm),
            'object': lm
        } for lm in loaded_models.values()])

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


def push_data_to_algolia(request: HttpRequest) -> HttpResponse:
    '''
    HTTP hook that pushes all data from DB to algolia.
    It's called hourly by an appengine job.
    '''
    call_command('push_data_to_algolia')
    return HttpResponse(status=204)


def page_not_found(request: HttpRequest) -> HttpResponse:
    '''Helper method to test 404 page rendering locally, where using real 404 shows stack trace.'''
    return views.defaults.page_not_found(request, None)


def robots_txt(request: HttpRequest) -> HttpResponse:
    '''
    Serve robots.txt
    https://developers.google.com/search/docs/advanced/robots/intro?hl=en
    '''
    context = {
        'host': request.get_host(),
        'protocol': 'https' if request.is_secure() else 'http'
    }
    return render(request, 'robots.txt', context)


def sitemap(request: HttpRequest) -> HttpResponse:
    '''
    Serve sitemap in text format.
    https://developers.google.com/search/docs/advanced/sitemaps/overview?hl=en
    '''
    pages: List[str] = ['/', '/about', '/catalog', '/articles']
    for article in ARTICLES:
        pages.append(reverse('single-article', args=(article.slug, )))
    for book in active_books():
        pages.append(reverse('book-detail-page', args=(book.slug, )))
    for person in Person.objects.all():
        pages.append(reverse('person-detail-page', args=(person.slug, )))
    for tag in Tag.objects.all():
        pages.append(reverse('catalog-for-tag', args=(tag.slug, )))
    for publisher in Publisher.objects.all():
        pages.append(reverse('publisher-detail-page', args=(publisher.slug, )))
    domain = 'https' if request.is_secure() else 'http'
    domain = domain + '://' + request.get_host()
    result = '\n'.join(domain + page for page in pages)
    return HttpResponse(result, content_type='text/plain')


DATA_JSON_FILE = 'tmp_data.json'


class UUIDEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def generate_data_json(request: HttpRequest) -> HttpResponse:
    '''
    HTTP hook that triggers generation of data.json file which
    will be cached and served by another handler.
    '''
    data: Dict = {
        'books':
        serializers.BookSimpleSerializer(
            Book.objects.prefetch_related('narrations').all(), many=True).data,
        'people':
        serializers.PersonSimpleSerializer(Person.objects.all(),
                                           many=True).data,
        'link_types':
        serializers.LinkTypeSimpleSerializer(LinkType.objects.all(),
                                             many=True).data,
        'tags':
        serializers.TagSerializer(Tag.objects.all(), many=True).data,
        'publishers':
        serializers.PublisherSimpleSerializer(Publisher.objects.all(),
                                              many=True).data
    }
    if default_storage.exists(DATA_JSON_FILE):
        default_storage.delete(DATA_JSON_FILE)

    data_str = json.dumps(data, ensure_ascii=False, indent=4, cls=UUIDEncoder)
    default_storage.save(DATA_JSON_FILE, ContentFile(data_str.encode('utf-8')))
    return HttpResponse(status=204)


@cache_control(max_age=60 * 60 * 24)
def get_data_json(request: HttpRequest) -> HttpResponse:
    '''
    Returns cached data.json that was generated by the generate_data_json
    handler.
    '''
    content = ''
    if default_storage.exists(DATA_JSON_FILE):
        with default_storage.open(DATA_JSON_FILE, 'r') as f:
            content = f.read()
    return HttpResponse(
        content,
        content_type='application/json',
        headers={
            # Allow accessing data.json from JS.
            'Access-Control-Allow-Origin': '*',
        })


def update_read_by_author_tag(request: HttpRequest) -> HttpResponse:
    '''
    HTTP hook that triggers update of 'Read by author tag'.
    '''
    read_by_author_tag = Tag.objects.filter(slug='cytaje-autar').first()
    if read_by_author_tag is None:
        return HttpResponse(status=500,
                            content='Tag cytaje-autar is missing from DB')
    books = Book.objects.prefetch_related('tag', 'narrations').all()
    book: Book
    read_by_author_tag.books.clear()
    for book in books:
        authors = set(book.authors.all())
        for narration in book.narrations.all():
            for narrator in narration.narrators.all():
                if narrator in authors:
                    read_by_author_tag.books.add(book)
    read_by_author_tag.save()
    return HttpResponse(status=204)


@require_POST
def markdown_to_html(request: HttpRequest) -> HttpResponse:
    '''Markdown to HTML'''
    markdown_text = request.body.decode('utf-8')
    if not markdown_text:
        return HttpResponse(content="Request body is empty",
                            content_type='text/plain',
                            status=400)
    html_text = markdownify(markdown_text, custom_settings="book_description")
    return HttpResponse(content=html_text,
                        content_type='text/html',
                        headers={'Access-Control-Allow-Origin': '*'})


@require_GET
def get_livelib_books(request: HttpRequest) -> HttpResponse:
    query = request.GET.get('query')
    if query:
        books = search_books_with_reviews(query)
    else:
        books = []
    return HttpResponse(content=json.dumps(books,
                                           ensure_ascii=False,
                                           indent=4,
                                           cls=DataclassJSONEncoder),
                        content_type='application/json',
                        headers={'Access-Control-Allow-Origin': '*'})


@csrf_exempt
def sync_image_cache(request: HttpRequest) -> HttpResponse:
    '''
    HTTP hook that triggers sync of image cache.
    '''
    sizes = image_cache.sync_cache()
    return HttpResponse(content=json.dumps(sizes, indent=4),
                        content_type='application/json')
