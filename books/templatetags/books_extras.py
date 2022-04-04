'''Various helper template filters for books.'''

from atexit import register
from typing import Optional
from zoneinfo import ZoneInfo
from django import template
from datetime import datetime
from django.utils import html

from books import models

register = template.Library()


@register.filter
def by_plural(value, variants):
    '''
    Chooses correct plural version of a wordt given number.
    variants is a comma-separated list of words.
    '''
    value = abs(int(value))

    if value % 10 == 1 and value % 100 != 11:
        variant = 0
    elif value % 10 >= 2 and value % 10 <= 4 and (value % 100 < 10
                                                  or value % 100 >= 20):
        variant = 1
    else:
        variant = 2

    return str(value) + ' ' + variants.split(',')[variant]


@register.filter
def gender(person: models.Person, variants: str):
    '''Choses correct ending of a gender-full word given comma-separated endings as "variants".'''
    if person.gender == 'FEMALE':
        variant = 0
    else:
        variant = 1

    return variants.split(',')[variant]


@register.filter
def duration(book: models.Book):
    '''Formats book duration using "36 hours 12 minutes" format.'''
    day = book.duration_sec.days
    seconds = book.duration_sec.seconds

    hrs = seconds // 3600
    mins = (seconds % 3600) // 60

    minutes = by_plural(mins, 'хвіліна,хвіліны,хвілін')

    if day:
        hrs = hrs + (day * 24)

    if hrs:
        hours = by_plural(hrs, 'гадзіна,гадзіны,гадзін')
        return f'{hours} {minutes}'

    return minutes


COVER_PATTERNS = [
    '/static/cover_templates/cover_templates_blue.jpeg',
    '/static/cover_templates/cover_templates_green.jpeg',
    '/static/cover_templates/cover_templates_grey.jpeg',
    '/static/cover_templates/cover_templates_purple.jpeg',
    '/static/cover_templates/cover_templates_red.jpeg',
    '/static/cover_templates/cover_templates_yellow.jpeg',
]


@register.filter
def colors(book: models.Book):
    '''Returns random cover template for a book that has no cover.'''
    return COVER_PATTERNS[book.uuid.int % len(COVER_PATTERNS)]


MONTHS = [
    'снежня', 'лютага', 'сакавіка', 'красавіка', 'траўня', 'чэрвеня', 'ліпеня',
    'жніўня', 'верасня', 'кастрычніка', 'лістапада', 'студзеня'
]


@register.simple_tag
def books_of_the_month():
    '''Returns text corresponding to current month.'''
    month = datetime.now(ZoneInfo('Europe/Minsk')).month
    return f'Кнігі {MONTHS[month - 1]}'


@register.simple_tag
def cite_source(source: str, cls: Optional[str]):
    '''
    Renders citation of a source.

    This tag is used to cite a photo or text when it's taken from
    another source. For example if book description is copied from
    another website.

    The format of source string is '<name>;<url>' where <name> is
    user-visible text.

    cls is a class to attach to the rendered <p> element for styling.
    '''
    if source == '':
        return ''
    parts = source.split(';')
    return html.format_html(
        '<p class="citation {}">Крыніца: <a href="{}">{}</a></p>', cls,
        parts[1], parts[0])
