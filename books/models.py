import functools
import os
from typing import Union
import uuid
import belorthography

from django.template import defaultfilters

from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.utils.translation import gettext as _

from books import image_cache


def lacinify(text: str) -> str:
    return belorthography.convert(text, belorthography.Orthography.OFFICIAL,
                                  belorthography.Orthography.LATIN_NO_DIACTRIC)


def _get_image_name(folder: str, instance: Union['Person', 'Book', 'Publisher',
                                                 'Narration'],
                    filename: str) -> str:
    '''Builds stored image file name based on the slug of the model.'''
    slug = isinstance(instance,
                      Narration) and instance.book.slug or instance.slug
    if isinstance(instance, Narration):
        slug += '-' + str(uuid.uuid4())
    extension = os.path.splitext(filename)[1]
    return os.path.join(folder, slug + extension)


class Gender(models.TextChoices):
    '''
    Gender of a person. Needed to correctly choose forms of some words as belarusian
    language has genders.
    '''
    FEMALE = 'FEMALE'
    MALE = 'MALE'
    # Represents person which is actually group of people. For example Dream-band "Агатка".
    PLURAL = 'PLURAL'


class Language(models.TextChoices):
    BELARUSIAN = 'BELARUSIAN'
    RUSSIAN = 'RUSSIAN'


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
                                          default='',
                                          validators=[
                                            RegexValidator(
                                                regex='^[^;]+;[^;]+$',
                                                message='Source must have format "caption;url"',
                                            ),
                                          ])
    photo = models.ImageField(upload_to=functools.partial(
        _get_image_name, 'photos'),
                              blank=True,
                              null=True)
    photo_source = models.CharField(_('Photo Source'),
                                    blank=True,
                                    max_length=500,
                                    default='',
                                    validators=[
                                        RegexValidator(
                                            regex='^[^;]+;[^;]+$',
                                            message='Source must have format "caption;url"',
                                        ),
                                    ])
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
    date_of_birth = models.DateField(_('Date of birth'),
                                     auto_now_add=False,
                                     blank=True,
                                     null=True)

    def __str__(self) -> str:
        return f'{self.name}'

    def save(self, *args, **kwargs):
        if self.slug != defaultfilters.slugify(self.slug) or self.slug == '':
            self.slug = defaultfilters.slugify(lacinify(self.name))
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
    description = models.TextField(_('Tag Description'), blank=True)

    hidden = models.BooleanField(_('Hidden'), default=False)

    def __str__(self) -> str:
        return f'{self.name}'

    def save(self, *args, **kwargs):
        self.tag_slug = defaultfilters.slugify(lacinify(self.name))
        super().save(*args, **kwargs)


class BookStatus(models.TextChoices):
    '''
    Status of abook. By default all books are active and visible but we need to hide it sometime.
    '''
    ACTIVE = 'ACTIVE'
    HIDDEN = 'HIDDEN'


class BookManager(models.Manager):
    def active_books_ordered_by_date(self) -> models.QuerySet:
        return (
            self
            .prefetch_related('authors')
            .filter(status=BookStatus.ACTIVE)
            # We order by nartation date. Books with the most recent narrations go first.
            .annotate(recent_annotation=models.Max('narrations__date'))
            .order_by('-recent_annotation')
        )


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
    title = models.CharField(_('Book Title'), max_length=100, default='')
    title_ru = models.CharField(_('Book Title in russian'),
                                max_length=100,
                                default='')
    description = models.TextField(_('Book Description'), blank=True)
    description_source = models.CharField(_('Book Description Source'),
                                          blank=True,
                                          max_length=500,
                                          default='',
                                          validators=[
                                            RegexValidator(
                                                regex='^[^;]+;[^;]+$',
                                                message='Source must have format "caption;url"',
                                            ),
                                          ])
    authors = models.ManyToManyField(Person, related_name='books_authored')
    slug = models.SlugField(_('slug'),
                            max_length=100,
                            unique=True,
                            db_index=True,
                            allow_unicode=True,
                            blank=True)
    tag = models.ManyToManyField(Tag, related_name='books', blank=True)
    promoted = models.BooleanField(_('Promoted'), default=False)
    status = models.CharField(_('Status'),
                              max_length=20,
                              choices=BookStatus.choices,
                              blank=False)
    preview_url = models.CharField(_('Preview URL'),
                                   max_length=100,
                                   blank=True,
                                   default='')
    livelib_url = models.CharField(_('LiveLib URL'),
                                   max_length=256,
                                   blank=True,
                                   default='')

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
            self.slug = defaultfilters.slugify(lacinify(self.title))
        super().save(*args, **kwargs)

    objects = BookManager()


class Publisher(models.Model):
    '''
    Publisher model.
    '''
    uuid = models.UUIDField(_('Publisher ID'),
                            primary_key=True,
                            default=uuid.uuid4,
                            editable=False,
                            unique=True)
    name = models.CharField(_('Publisher Name'), max_length=100, default='')
    slug = models.SlugField(_('Publisher Slug'),
                            max_length=100,
                            unique=True,
                            db_index=True,
                            allow_unicode=True,
                            blank=True)
    url = models.URLField(_('Publisher Website'), max_length=128)
    logo = models.ImageField(upload_to=functools.partial(
        _get_image_name, 'logos'),
                             blank=True,
                             null=True)
    description = models.TextField(_('Publisher Description'), blank=True)

    def __str__(self) -> str:
        return f'{self.name}'

    def save(self, *args, **kwargs):
        if self.slug != defaultfilters.slugify(self.slug) or self.slug == '':
            self.slug = defaultfilters.slugify(lacinify(self.name))
        super().save(*args, **kwargs)


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
    translators = models.ManyToManyField(Person,
                                         related_name='narrations_translated',
                                         blank=True)
    book = models.ForeignKey(Book,
                             related_name='narrations',
                             on_delete=CASCADE)

    paid = models.BooleanField(_('Is narration paid?'), default=False)

    language = models.CharField(_('Language'),
                                max_length=20,
                                choices=Language.choices,
                                blank=False)

    duration = models.DurationField(_('Duration'), blank=True, null=True)

    publishers = models.ManyToManyField(Publisher,
                                        related_name='narrations',
                                        blank=True)

    description = models.TextField(_('Narration Description'), blank=True)

    cover_image = models.ImageField(upload_to=functools.partial(
        _get_image_name, 'covers'),
                                    blank=True,
                                    null=True)

    cover_image_source = models.CharField(_('Cover Source'),
                                          blank=True,
                                          max_length=500,
                                          default='',
                                          validators=[
                                            RegexValidator(
                                                regex='^[^;]+;[^;]+$',
                                                message='Source must have format "caption;url"',
                                            ),
                                          ])

    date = models.DateField(_('Release Date'), auto_now_add=False, null=False)

    def __str__(self) -> str:
        return '%s read by %s' % (
            self.book,
            ', '.join(narrator.name for narrator in self.narrators.all()),
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        image_cache.trigger_image_resizing()


class LinkAvailability(models.TextChoices):
    '''
    Enum representing where the link is available. For example it can be unavailable in Belarus.
    '''
    EVERYWHERE = 'EVERYWHERE'
    UNAVAILABLE_IN_BELARUS = 'UNAVAILABLE_IN_BELARUS'
    USA_ONLY = 'USA_ONLY'


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
    disabled = models.BooleanField(_('Disabled'), default=False)
    url_regex = models.CharField(_('Url regex'),
                                 max_length=100,
                                 blank=True,
                                 default='')
    availability = models.CharField(_('Availability'),
                                    max_length=50,
                                    choices=LinkAvailability.choices,
                                    blank=False)
    weight = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(1),
                                MaxValueValidator(100)])

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
    url = models.URLField(_('URL'), max_length=1024)
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
