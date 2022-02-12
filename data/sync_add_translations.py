'''Fills russian translation for books and authors names using TRANSLATIONS_STRING string'''

from typing import Dict, Set
from data import books

TRANSLATIONS_STRING = '''Алесь Разанаў	Алесь Рязанов'''


def run(data: books.BooksData) -> None:
    '''See description in module comment.'''
    translations: Dict[str, str] = {}
    for line in TRANSLATIONS_STRING.split('\n'):
        parts = line.split('\t')
        translations[parts[0]] = parts[1]
    used_translations: Set[str] = set()
    for person in data.people:
        name = person.name
        if name in translations:
            person.name_ru = translations[name]
            person.save()
            used_translations.add(name)
    for book in data.books:
        title = book.title
        if title in translations:
            book.title_ru = translations[title]
            book.save()
            used_translations.add(title)
    for key in translations.keys():
        if not key in used_translations:
            print(f'Translations for {key} is not used')