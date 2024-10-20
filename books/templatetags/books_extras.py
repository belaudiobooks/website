"""Various helper template filters for books."""

from typing import Optional, Sequence
from django import template
from datetime import datetime
from django.utils import html
from django.utils.translation import get_language
from django.utils.translation import gettext as _
import belorthography

from books import models, image_cache
from books.constants import MONTHS

register = template.Library()


@register.filter
def by_plural(value, variants) -> str:
    """
    Chooses correct plural version of a wordt given number.
    variants is a comma-separated list of words.
    """
    value = abs(int(value))

    if value % 10 == 1 and value % 100 != 11:
        variant = 0
    elif (
        value % 10 >= 2 and value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20)
    ):
        variant = 1
    else:
        variant = 2

    return str(value) + " " + variants.split(",")[variant]


@register.filter
def gender(persons: Sequence[models.Person] | models.Person, variants: str) -> str:
    """Choses correct ending of a gender-full word given comma-separated endings as "variants"."""
    if isinstance(persons, models.Person):
        gender = persons.gender
    else:
        gender = models.Gender.PLURAL if persons.count() > 1 else persons[0].gender
    if gender == models.Gender.FEMALE:
        variant = 0
    elif gender == models.Gender.MALE:
        variant = 1
    elif gender == models.Gender.PLURAL:
        variant = 2
    else:
        raise ValueError(f"Gender {gender} is not supported")

    return variants.split(",")[variant]


@register.filter
def to_human_language(lang: str) -> str:
    """Converts Language enum to human readable language string."""
    if lang == models.Language.BELARUSIAN:
        return "беларуская"
    elif lang == models.Language.RUSSIAN:
        return "руская"
    else:
        raise ValueError("Uknown language " + lang)


@register.filter
def link_type_availibility(availability: str) -> str:
    """Converts link availability enum to human readable."""
    if availability == models.LinkAvailability.EVERYWHERE:
        return ""
    elif availability == models.LinkAvailability.UNAVAILABLE_IN_BELARUS:
        return "не працуе ў Беларусі"
    elif availability == models.LinkAvailability.USA_ONLY:
        return "толькі ў ЗША"
    else:
        raise ValueError("Uknown avalability " + availability)


@register.filter
def duration(narration: models.Narration) -> str:
    """Formats book duration using "36 hours 12 minutes" format."""
    day = narration.duration.days
    seconds = narration.duration.seconds

    hrs = seconds // 3600
    mins = (seconds % 3600) // 60

    minutes = by_plural(mins, "хвіліна,хвіліны,хвілін")

    if day:
        hrs = hrs + (day * 24)

    if hrs:
        hours = by_plural(hrs, "гадзіна,гадзіны,гадзін")
        return f"{hours} {minutes}"

    return minutes


COVER_PATTERNS = [
    "/static/cover_templates/cover_templates_blue.jpeg",
    "/static/cover_templates/cover_templates_green.jpeg",
    "/static/cover_templates/cover_templates_grey.jpeg",
    "/static/cover_templates/cover_templates_purple.jpeg",
    "/static/cover_templates/cover_templates_red.jpeg",
    "/static/cover_templates/cover_templates_yellow.jpeg",
]


@register.filter
def colors(narration: models.Narration, ind=0) -> str:
    """Returns random cover template for a narration that has no cover."""
    return COVER_PATTERNS[(narration.book.uuid.int + ind) % len(COVER_PATTERNS)]


@register.filter
def format_date(date: datetime.date, format: str) -> str:
    """Formats date in a human-readable format."""
    contains_day = format.find("d") != -1
    month = MONTHS[date.month - 1][1] if contains_day else MONTHS[date.month - 1][0]
    return (
        format.replace("d", str(date.day))
        .replace("m", month)
        .replace("Y", str(date.year))
    )


@register.simple_tag
def cite_source(source: str, cls: Optional[str]):
    """
    Renders citation of a source.

    This tag is used to cite a photo or text when it's taken from
    another source. For example if book description is copied from
    another website.

    The format of source string is '<name>;<url>' where <name> is
    user-visible text.

    cls is a class to attach to the rendered <p> element for styling.
    """
    if source == "" or source.count(";") != 1:
        return ""
    parts = source.split(";")
    source = _("Крыніца")
    return html.format_html(
        '<p class="mb-3 citation {}">{}: <a href="{}">{}</a></p>',
        cls,
        source,
        parts[1],
        parts[0],
    )


@register.filter
def resized_image(source: str, type: str) -> str:
    """
    Returns URL of resized image.

    If image is not resized yet, returns original URL.
    """
    if type == "small":
        return image_cache.get_image_for_size(source, 300)
    elif type == "large":
        return source
    else:
        raise ValueError("Unknown image type " + type)


@register.filter
def narration_for_prevview(book: models.Book) -> Optional[models.Narration]:
    """Returns narration that should be displayed for a book in preview."""
    if book.narrations.count() == 0:
        return None
    if book.narrations.count() == 1:
        return book.narrations.first()
    return book.narrations.order_by("-date").first()


OVERLAP_COVER_OFFSET = 20


@register.filter
def cover_offset(ind: int) -> int:
    """Returns offset of a cover given its index in the list of narrations."""
    return (ind - 1) * OVERLAP_COVER_OFFSET


@register.filter
def overlapping_cover_scale(book: models.Book) -> float:
    """Returns scale of a cover that should be used when displaying preview with multiple narrations.

    When there are multiple narrations - we show them overlapped and but they need to fit 150x150px box.
    Thus we need to scale them down.
    """
    return 1 - (book.narrations.count() - 1) * OVERLAP_COVER_OFFSET / 150


@register.simple_tag
def dtranslate(text: str):
    if get_language() == "be-latn":
        return belorthography.convert(
            text, belorthography.Orthography.OFFICIAL, belorthography.Orthography.LATIN
        )
    else:
        return text
