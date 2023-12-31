'''
See Command desription.
'''

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from algoliasearch.search_client import SearchClient
from books import models
import belorthography


def _person_has_active_books(person: models.Person) -> bool:
    books = list(person.books_authored.all())
    related_narrations = person.narrations.all().union(person.narrations_translated.all())
    books += [n.book for n in related_narrations]
    active_books = filter(lambda b: b.status == models.BookStatus.ACTIVE,
                          books)
    return any(active_books)


def _publisher_has_active_books(publisher: models.Publisher) -> bool:
    books = [n.book for n in publisher.narrations.all()]
    active_books = filter(lambda b: b.status == models.BookStatus.ACTIVE,
                          books)
    return any(active_books)

def _lacinify(text: str) -> str:
    return belorthography.convert(
        text,
        belorthography.Orthography.OFFICIAL,
        belorthography.Orthography.LATIN
    )

class Command(BaseCommand):
    '''See help.'''

    help = 'Pushes data to algolia. Expects that algolia settings will be set.'

    def handle(self, *args, **options):
        if settings.ALGOLIA_APPLICATION_ID == '' or settings.ALGOLIA_MODIFY_KEY == '':
            raise CommandError(
                'Algolia keys are not set. Check Algolia section in README.')
        # Start the API client
        # https://www.algolia.com/doc/api-client/getting-started/instantiate-client-index/
        client = SearchClient.create(settings.ALGOLIA_APPLICATION_ID,
                                     settings.ALGOLIA_MODIFY_KEY)

        # Create an index (or connect to it, if an index with the name `ALGOLIA_INDEX_NAME`
        # already exists)
        # https://www.algolia.com/doc/api-client/getting-started/instantiate-client-index/#initialize-an-index
        index = client.init_index(settings.ALGOLIA_INDEX)

        data = []
        books = models.Book.objects.filter(
            status=models.BookStatus.ACTIVE).prefetch_related('authors')
        for book in books:
            authors = [author.name for author in book.authors.all()]
            authors_ru = [author.name_ru for author in book.authors.all()]
            authors_lac = [_lacinify(author.name) for author in book.authors.all()]
            data.append({
                'objectID': book.uuid,
                'model': 'book',
                'title': book.title,
                'title_ru': book.title_ru,
                'title_lac': _lacinify(book.title),
                'slug': book.slug,
                'authors': authors,
                'authors_ru': authors_ru,
                'authors_lac': authors_lac,
            })
        people = models.Person.objects.all().prefetch_related(
            'books_authored', 'narrations_translated', 'narrations')
        for person in people:
            if not _person_has_active_books(person):
                continue

            data.append({
                'objectID': person.uuid,
                'model': 'person',
                'name': person.name,
                'name_ru': person.name_ru,
                'name_lac': _lacinify(person.name),
                'slug': person.slug,
            })
        publishers = models.Publisher.objects.all()
        for publisher in publishers:
            if not _publisher_has_active_books(publisher):
                continue
            data.append({
                'objectID': publisher.uuid,
                'model': 'publisher',
                'name': publisher.name,
                'name_lac': _lacinify(publisher.name),
                'slug': publisher.slug,
            })
        print(
            f'Pushing {len(data)} objects to index "{settings.ALGOLIA_INDEX}"...'
        )
        res = index.replace_all_objects(data)
        res.wait()
        print('Completed!')
