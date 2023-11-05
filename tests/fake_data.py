from datetime import date, timedelta
import tempfile
from typing import List
from books import models
from django.core.files.uploadedfile import SimpleUploadedFile


class FakeData:
    """Class initializing fake data for testing.

    The class runs at the start of each test and creates few standard objects in DB that
    can be used across all tests. Individual tests are expected to create books and narrations
    themselves as those are usually specific to the test."""

    def __init__(self):
        """Initialize fake data."""

        self.tag_poetry = models.Tag.objects.create(
            name='паэзія',
            slug='poezia',
        )
        self.tag_fiction = models.Tag.objects.create(
            name='фантастыка',
            slug='fiction',
        )
        self.tag_read_by_author = models.Tag.objects.create(
            name='чытае аўтар',
            slug='cytaje-autar',
        )

        self.link_type_knizhny_voz = models.LinkType.objects.create(
            name='knizny_voz',
            caption='Кніжны Воз',
            icon=SimpleUploadedFile(
                tempfile.NamedTemporaryFile(suffix=".jpg").name, b""),
            availability=models.LinkAvailability.EVERYWHERE,
        )
        self.link_type_kobo = models.LinkType.objects.create(
            name='kobo',
            caption='Kobo',
            icon=SimpleUploadedFile(
                tempfile.NamedTemporaryFile(suffix=".jpg").name, b""),
            availability=models.LinkAvailability.EVERYWHERE,
        )

        self.person_ales = models.Person.objects.create(
            name='Алесь Алесявіч',
            name_ru='Александр Алесевич',
            slug='ales-alesievich',
        )
        self.person_bela = models.Person.objects.create(
            name='Бэла Бэлаўна',
            name_ru='Белла Беловна',
            slug='bela-belawna',
        )
        self.person_viktar = models.Person.objects.create(
            name='Віктар Віктаравіч',
            name_ru='Виктор Викторович',
            slug='viktar-viktavarich',
        )

        self.publisher_audiobooksby = models.Publisher.objects.create(
            name="audiobooks.by",
            slug="audiobooksby",
            url="https://audiobooks.by/about",
            logo=SimpleUploadedFile(
                tempfile.NamedTemporaryFile(suffix=".jpg").name, b""),
            description="Мы - каманда энтузіястаў.")

    def create_image(self) -> SimpleUploadedFile:
        return SimpleUploadedFile(
            tempfile.NamedTemporaryFile(suffix=".jpg").name, b"")

    def cleanup(self):
        for link_type in models.LinkType.objects.all():
            link_type.icon.delete()
        for publisher in models.Publisher.objects.all():
            publisher.logo.delete()
        for person in models.Person.objects.all():
            person.photo.delete()
        for narration in models.Narration.objects.all():
            narration.cover_image.delete()

    def create_link(self, link_type: models.LinkType,
                    book: models.Book) -> models.Link:
        return models.Link.objects.create(
            url=f'https://{link_type.name}.com/{book.slug}',
            url_type=link_type,
        )

    def create_book_with_single_narration(
            self,
            title: str,
            authors: List[models.Person] = [],
            translators: List[models.Person] = [],
            narrators: List[models.Person] = [],
            tags: List[models.Tag] = [],
            link_types: List[models.LinkType] = [],
            language: models.Language = models.Language.BELARUSIAN,
            publishers: List[models.Publisher] = [],
            date=date.today(),
            duration: timedelta = timedelta(minutes=15),
            paid: bool = False,
            livelib_url: str = ''
    ):
        book = models.Book.objects.create(
            title=title,
            title_ru=f'{title} по-русски',
            date=date,
            status=models.BookStatus.ACTIVE,
            livelib_url=livelib_url
        )
        book.authors.set(authors)
        book.translators.set(translators)
        book.tag.set(tags)
        narration = models.Narration.objects.create(
            language=language,
            duration=duration,
            book=book,
            paid=paid,
        )
        narration.narrators.set(narrators)
        narration.publishers.set(publishers)
        for link_type in link_types:
            narration.links.add(self.create_link(link_type, narration.book))
        narration.save()
        return book
