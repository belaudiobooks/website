import functools
import os
from typing import Union
import uuid

from unidecode import unidecode
from django.template import defaultfilters

from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.utils.translation import gettext as _
from .managers import BookManager


def _get_image_name(folder: str, instance: Union['Person', 'Book'],
                    filename: str) -> str:
    '''Builds stored image file name based on the slug of the model.'''
    extension = os.path.splitext(filename)[1]
    return os.path.join(folder, instance.slug + extension)


class Gender(models.TextChoices):
    '''
    Gender of a person. Needed to correctly choose forms of some words as belarusian
    language has genders.
    '''
    FEMALE = 'FEMALE'
    MALE = 'MALE'
    # Represents person which is actually group of people. For example Dream-band "Агатка".
    PLURAL = 'PLURAL'


class Person(models.Model):
    '''
    Model representing single person. Person can perform multiple roles, like being an
    author, translator or narrator. Those roles aren't set on person, but can be derived
    from fields in other models, like Book.authors.
    '''
    uuid = models.UUIDField(_('Person Id'),
                            primary_key=True,
                            default=uuid.uuid4,
                            editable=False,
                            unique=True)
    name = models.CharField(_('Person Name'), max_length=100, default='')
    name_ru = models.CharField(_('Person Name in russian'),
                               max_length=100,
                               default='')
    description = models.TextField(_('Person Description'), blank=True)
    description_source = models.CharField(_('Person Description Source'),
                                          blank=True,
                                          max_length=500,
                                          default='')
    photo = models.ImageField(upload_to=functools.partial(
        _get_image_name, 'photos'),
                              blank=True,
                              null=True)
    photo_source = models.CharField(_('Photo Source'),
                                    blank=True,
                                    max_length=500,
                                    default='')
    slug = models.SlugField(_('Person slug'),
                            max_length=100,
                            unique=True,
                            db_index=True,
                            allow_unicode=True,
                            blank=True)
    gender = models.CharField(_('Person gender'),
                              max_length=20,
                              choices=Gender.choices,
                              blank=False)

    def __str__(self) -> str:
        return f'{self.name}'

    def save(self, *args, **kwargs):
        if self.slug != defaultfilters.slugify(self.slug) or self.slug == '':
            self.slug = defaultfilters.slugify(unidecode(self.name))
        super().save(*args, **kwargs)


class Tag(models.Model):
    '''
    Tag is a group of books that have some common trait. For example different genres are
    examples of tags. Each book can and should have one or more tags.
    '''
    name = models.CharField(_('Tag'), max_length=50, default='')
    slug = models.SlugField(_('Tag slug'),
                            max_length=100,
                            allow_unicode=True,
                            blank=True)

    def __str__(self) -> str:
        return f'{self.name}'

    def save(self, *args, **kwargs):
        self.tag_slug = defaultfilters.slugify(unidecode(self.name))
        super().save(*args, **kwargs)


class BookStatus(models.TextChoices):
    '''
    Status of abook. By default all books are active and visible but we need to hide it sometime.
    '''
    ACTIVE = 'ACTIVE'
    HIDDEN = 'HIDDEN'


class Book(models.Model):
    '''
    Book model represents a single book... It can have multiple authors and or translators. Single
    books can have multiple narrations if it was narrated by different groups of people. Each book
    should have at least one Narration.
    '''
    uuid = models.UUIDField(_('Book ID'),
                            primary_key=True,
                            default=uuid.uuid4,
                            editable=False,
                            unique=True)
    title = models.CharField(_('Book Title'),
                             max_length=100,
                             blank=True,
                             default='')
    title_ru = models.CharField(_('Book Title in russian'),
                                max_length=100,
                                blank=True,
                                default='')
    description = models.TextField(_('Book Description'), blank=True)
    description_source = models.CharField(_('Book Description Source'),
                                          blank=True,
                                          max_length=500,
                                          default='')
    added_at = models.DateTimeField(_('Added at'), auto_now_add=True)
    date = models.DateField(_('Book Date'), auto_now_add=False)
    authors = models.ManyToManyField(Person, related_name='books_authored')
    translators = models.ManyToManyField(Person,
                                         related_name='books_translated',
                                         blank=True)
    slug = models.SlugField(_('slug'),
                            max_length=100,
                            unique=True,
                            db_index=True,
                            allow_unicode=True,
                            blank=True)
    cover_image = models.ImageField(upload_to=functools.partial(
        _get_image_name, 'covers'),
                                    blank=True,
                                    null=True)
    cover_image_source = models.CharField(_('Cover Image Source'),
                                          blank=True,
                                          max_length=500,
                                          default='')
    tag = models.ManyToManyField(Tag, related_name='tag', blank=True)
    promoted = models.BooleanField(_('Promoted'), default=False)
    duration_sec = models.DurationField(_('Duration'), blank=True, null=True)
    status = models.CharField(_('Status'),
                              max_length=20,
                              choices=BookStatus.choices,
                              blank=False)

    def __str__(self) -> str:
        return "%s (%s)" % (
            self.title,
            ", ".join(author.name for author in self.authors.all()),
        )
        # f'{self.authors.all()[0]} - {self.title}'

    def save(self, *args, **kwargs):
        # Update slug only if current slug uses belarusian letters (created in admin).
        # Otherwise don't update slug as it might be intentionally set to be different
        # from title.
        if self.slug != defaultfilters.slugify(self.slug) or self.slug == '':
            self.slug = defaultfilters.slugify(unidecode(self.title))
        super().save(*args, **kwargs)

    objects = BookManager()


class Narration(models.Model):
    '''
    Narration represents particular narration of a book. It's represented through a separate model so
    that we can visually separate narrations in UI. As different narration fo the same books have different
    narrators and set of links.
    '''
    uuid = models.UUIDField(_('Narration ID'),
                            primary_key=True,
                            default=uuid.uuid4,
                            editable=False,
                            unique=True)
    narrators = models.ManyToManyField(Person,
                                       related_name='narrations',
                                       blank=True)
    book = models.ForeignKey(Book,
                             related_name='narrations',
                             blank=True,
                             null=True,
                             on_delete=SET_NULL)

    def __str__(self) -> str:
        return '%s read by %s' % (
            self.book,
            ', '.join(narrator.name for narrator in self.narrators.all()),
        )


class LinkType(models.Model):
    '''
    LinkType represents a particular source in internet where audibooks are hosted. Examples are
    Google podcasts, apple podcasts, Knizhny Voz, LitRes.
    '''
    name = models.CharField(_('Link Type Name'),
                            max_length=70,
                            blank=True,
                            default='')
    caption = models.CharField(_('Link Caption'),
                               max_length=100,
                               blank=True,
                               default='')
    icon = models.ImageField(upload_to='icons', blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.name}'


class Link(models.Model):
    '''
    Link represents a URL link that points to page where users can find and listen to an audiobook.
    For example it can be link to particular Google Podcast or audiobook page on LitRes.
    '''
    uuid = models.UUIDField(_('Link Id'),
                            primary_key=True,
                            default=uuid.uuid4,
                            editable=False,
                            unique=True)
    url = models.URLField(_('URL'), max_length=300)
    url_type = models.ForeignKey(LinkType,
                                 related_name='link_type',
                                 null=True,
                                 on_delete=SET_NULL)
    narration = models.ForeignKey(Narration,
                                  related_name="links",
                                  on_delete=CASCADE,
                                  null=True)

    def __str__(self) -> str:
        return f'{self.url} - {self.url_type}'
