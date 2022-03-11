'''
See Command desription.
'''

from django.core.management.base import BaseCommand
from django.conf import settings
from algoliasearch.search_client import SearchClient
from books import models


class Command(BaseCommand):
    '''See help.'''

    help = 'Pushes data to algolia. Expects that algolia settings will be set.'

    def handle(self, *args, **options):
        # Start the API client
        # https://www.algolia.com/doc/api-client/getting-started/instantiate-client-index/
        client = SearchClient.create(settings.ALGOLIA_APPLICATION_ID,
                                     settings.ALGOLIA_MODIFY_KEY)

        # Create an index (or connect to it, if an index with the name `ALGOLIA_INDEX_NAME` already exists)
        # https://www.algolia.com/doc/api-client/getting-started/instantiate-client-index/#initialize-an-index
        index = client.init_index(settings.ALGOLIA_INDEX)

        data = []
        for book in models.Book.objects.all().prefetch_related('authors'):
            authors = [author.name for author in book.authors.all()]
            authors_ru = [author.name_ru for author in book.authors.all()]
            data.append({
                'objectID': book.uuid,
                'model': 'book',
                'title': book.title,
                'title_ru': book.title_ru,
                'slug': book.slug,
                'authors': authors,
                'authors_ru': authors_ru,
            })
        for person in models.Person.objects.all():
            data.append({
                'objectID': person.uuid,
                'model': 'person',
                'name': person.name,
                'name_ru': person.name_ru,
                'slug': person.slug,
            })
        print(f'Pushing {len(data)} objects...')
        res = index.replace_all_objects(data)
        res.wait()
        print('Completed!')
