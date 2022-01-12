import uuid

from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.fields import TextField
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.urls import reverse


class Person(models.Model):
    uuid = models.UUIDField(_("person_id"), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(_('person_name'), max_length=100, default='')
    description = models.TextField(_('person_description'))


class Genre(models.Model):
    name = models.CharField

    def __str__(self) -> str:
        return f'{self.name}'

class Book(models.Model):
    uuid = models.UUIDField(_("book_id"), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(_('title'), max_length=100, blank=True, default='')
    description = models.TextField(_('book_description'))
    date = models.DateTimeField(_('created_at'), auto_now_add=False)
    authors = models.ManyToManyField(Person, related_name='authors')
    narrators = models.ManyToManyField(Person, related_name='narrators')
    translators = models.ManyToManyField(Person, related_name='translators')
    slug = models.SlugField(_('slug'), unique=True, db_index=True, null=False)
    cover_image_name = models.CharField(max_length=50)
    genre = models.ManyToManyField(Genre, related_name='genre')
    promoted = models.BooleanField(_(''), default=False)
    annotation = TextField(_('book_annotation'))
    
    def __str__(self) -> str:
        return f'{self.authors} - {self.title}'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class LinkType(models.Model):
    name = models.CharField(_('link_type'), max_length=70, blank=True, default='')
    caption = models.CharField(_('link_caption'), max_length=100, blank=True, default='')
    icon_name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return f'{self.name}'

class Link(models.Model):
    uuid = models.UUIDField(_("link_id"), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    url = models.URLField(_("url"), max_length=300)
    url_type = models.ForeignKey(LinkType, null=True, on_delete=SET_NULL)
    book = models.ForeignKey(Book, on_delete=CASCADE)

    def __str__(self) -> str:
        return f'{self.url} - {self.type}'
