import uuid

from unidecode import unidecode
from django.template import defaultfilters

from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.fields import TextField
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.urls import reverse


class Person(models.Model):
    uuid = models.UUIDField(_('Person Id'), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(_('Person Name'), max_length=100, default='')
    description = models.TextField(_('Person Description'))
    photo = models.ImageField(upload_to='photos', null=True)

    def __str__(self) -> str:
        return f'{self.name}'


class Genre(models.Model):
    name = models.CharField(_('Genre Name'), max_length=50, default='')

    def __str__(self) -> str:
        return f'{self.name}'


class Book(models.Model):
    uuid = models.UUIDField(_('Book ID'), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(_('Book Title'), max_length=100, blank=True, default='')
    description = models.TextField(_('Book Description'))
    added_at = models.DateTimeField(_('Added at'), auto_now_add=True)
    date = models.DateField(_('Book Date'), auto_now_add=False)
    authors = models.ManyToManyField(Person, related_name='authors')
    narrators = models.ManyToManyField(Person, related_name='narrators', blank=True)
    translators = models.ManyToManyField(Person, related_name='translators', blank=True)
    slug = models.SlugField(_('slug'), unique=True, db_index=True, allow_unicode=True, blank=True)
    cover_image = models.ImageField(upload_to='covers', null=True)
    genre = models.ManyToManyField(Genre, related_name='genre')
    promoted = models.BooleanField(_('Promoted'), default=False)
    annotation = TextField(_('Book Annotation'), blank=True)
    
    def __str__(self) -> str:
        return f'{self.authors.all()[0]} - {self.title}'

    def save(self, *args, **kwargs):
        self.slug = defaultfilters.slugify(unidecode(self.title))
        super().save(*args, **kwargs)


class LinkType(models.Model):
    name = models.CharField(_('Link Type Name'), max_length=70, blank=True, default='')
    caption = models.CharField(_('Link =Caption'), max_length=100, blank=True, default='')
    icon = models.ImageField(upload_to='icons', null=True)

    def __str__(self) -> str:
        return f'{self.name}'


class Link(models.Model):
    uuid = models.UUIDField(_('Link Id'), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    url = models.URLField(_('URL'), max_length=300)
    url_type = models.ForeignKey(LinkType, null=True, on_delete=SET_NULL)
    book = models.ForeignKey(Book, on_delete=CASCADE)

    def __str__(self) -> str:
        return f'{self.url} - {self.url_type}'
