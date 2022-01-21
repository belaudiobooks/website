import uuid

from unidecode import unidecode
from django.template import defaultfilters

from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.utils.translation import gettext as _
from .managers import BookManager


class Person(models.Model):
    uuid = models.UUIDField(_('Person Id'), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(_('Person Name'), max_length=100, default='')
    description = models.TextField(_('Person Description'))
    photo = models.ImageField(upload_to='photos', blank=True, null=True)
    slug = models.SlugField(_('Person slug'), unique=True, db_index=True, allow_unicode=True, blank=True)

    def __str__(self) -> str:
        return f'{self.name}'
    
    def save(self, *args, **kwargs):
        self.slug = defaultfilters.slugify(unidecode(self.name))
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(_('Tag'), max_length=50, default='')

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
    cover_image = models.ImageField(upload_to='covers', blank=True, null=True)
    tag = models.ManyToManyField(Tag, related_name='tag')
    promoted = models.BooleanField(_('Promoted'), default=False)
    annotation = models.TextField(_('Book Annotation'), blank=True)
    duration_sec = models.DurationField(_('Duration'), blank=True, null=True)
    
    def __str__(self) -> str:
        return "%s (%s)" % (
            self.title,
            ", ".join(author.name for author in self.authors.all()),
        )
        # f'{self.authors.all()[0]} - {self.title}'

    def save(self, *args, **kwargs):
        self.slug = defaultfilters.slugify(unidecode(self.title))
        super().save(*args, **kwargs)

    objects = BookManager()


class LinkType(models.Model):
    name = models.CharField(_('Link Type Name'), max_length=70, blank=True, default='')
    caption = models.CharField(_('Link =Caption'), max_length=100, blank=True, default='')
    icon = models.ImageField(upload_to='icons', blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.name}'


class Link(models.Model):
    uuid = models.UUIDField(_('Link Id'), primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    url = models.URLField(_('URL'), max_length=300)
    url_type = models.ForeignKey(LinkType, null=True, on_delete=SET_NULL)
    book = models.ForeignKey(Book, on_delete=CASCADE)

    def __str__(self) -> str:
        return f'{self.url} - {self.url_type}'
