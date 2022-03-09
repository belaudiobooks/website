'''
Module to generate JSON data for Algolia search. It saves result in /tmp/algolia.json file to be 
manually uploaded to algolia later.
'''
import json

from . import books


def run(data: books.BooksData) -> None:
    '''See description in module.'''
    result = []
    for book in data.books:
        authors = [author.name for author in book.authors.all()]
        result.append({
            'model': 'book',
            'title': book.title,
            'title_ru': book.title_ru,
            'slug': book.slug,
            'authors': authors,
        })
    for person in data.people:
        result.append({
            'model': 'person',
            'name': person.name,
            'name_ru': person.name_ru,
            'slug': person.slug,
        })
    with open('/tmp/algolia.json', 'w', encoding='utf8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print('wrote algolia data to /tmp/algolia.json')
