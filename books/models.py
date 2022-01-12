from io import open_code
import uuid

from django.db import models
from django.db.models.deletion import CASCADE, SET_DEFAULT, SET_NULL
from django.db.models.fields import TextField
from django.db.models.fields.related import ForeignKey, OneToOneField
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.urls import reverse


class Person(models.Model):
    uuid = models.UUIDField(_("person_id"), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField
    description = models.TextField


class Genre(models.Model):
    name = models.CharField

    def __str__(self) -> str:
        return f'{self.name}'

class Book(models.Model):
    uuid = models.UUIDField(_("book_id"), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(_('title'), max_length=70, blank=True, default='')
    description = models.TextField(_('text'))
    date = models.DateTimeField(_('created_at'), auto_now_add=False)
    authors = models.ManyToManyField(Person)
    narrators = models.ManyToManyField(Person)
    translators = models.ManyToManyField(Person)
    slug = models.SlugField(_('slug'), unique=True, db_index=True, default='', null=False)
    cover_url = models.URLField(_(''))
    genre = models.ManyToManyField(Genre)
    promoted = models.BooleanField(_(''), default=False)
    annotation = TextField(_('annotation'))

    # def get_absolute_url(self):
    #     return reverse("book_detail", args=[self.uuid])
    
    def __str__(self) -> str:
        return f'{self.authors} - {self.title}'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)



class LinkType(models.Model):
    uuid = models.UUIDField(_("type_id"), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField
    caption = models.CharField
    icon_url = models.URLField

    def __str__(self) -> str:
        return f'{self.name}'

class Link(models.Model):
    uuid = models.UUIDField(_("link_id"), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    url = models.URLField(_("url"), max_length=200)
    url_type = models.ForeignKey(LinkType, on_delete=SET_NULL)
    book = models.ForeignKey(Book, on_delete=CASCADE)

    def __str__(self) -> str:
        return f'{self.url} - {self.type}'
