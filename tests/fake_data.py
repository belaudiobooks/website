import tempfile
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

    def cleanup(self):
        for link_type in models.LinkType.objects.all():
            link_type.icon.delete()
        for publisher in models.Publisher.objects.all():
            publisher.logo.delete()

    def create_link(self, link_type: models.LinkType,
                    book: models.Book) -> models.Link:
        return models.Link.objects.create(
            url=f'https://{link_type.name}.com/{book.slug}',
            url_type=link_type,
        )
