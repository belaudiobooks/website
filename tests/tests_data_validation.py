from tests.fake_data import FakeData
from tests.webdriver_test_case import WebdriverTestCase

import requests


class DataValidationTests(WebdriverTestCase):
    """Tests that validate data."""

    def test_data_json_generates(self):
        self.maxDiff = None
        fake_data: FakeData = self.fake_data
        publisher = fake_data.publisher_audiobooksby
        book = fake_data.create_book_with_single_narration(
            title="Book 1",
            authors=[fake_data.person_ales],
            narrators=[fake_data.person_bela],
            translators=[fake_data.person_viktar],
            publishers=[publisher],
            link_types=[fake_data.link_type_kobo],
            date="2023-11-06",
            tags=[fake_data.tag_classics],
        )
        book.description = "Book description"
        book.save()

        narration = book.narrations.first()
        narration.description = "Narration description"
        narration.date = "2023-11-07"
        narration.paid = True
        narration.preview_url = "https://youtube.com/"
        narration.save()

        fake_data.person_ales.description = "Ales description"
        fake_data.person_ales.save()

        response = requests.get(
            f"{self.live_server_url}/job/generate_data_json", timeout=20
        )
        self.assertEqual(204, response.status_code)

        response = requests.get(f"{self.live_server_url}/data.json", timeout=20)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {
                "books": [
                    {
                        "authors": [str(fake_data.person_ales.uuid)],
                        "description": "Book description",
                        "description_source": "",
                        "narrations": [
                            {
                                "cover_image": None,
                                "description": "Narration description",
                                "cover_image_source": "",
                                "date": "2023-11-07",
                                "duration": 900.0,
                                "language": "BELARUSIAN",
                                "links": [
                                    {
                                        "url": "https://kobo.com/book-1",
                                        "url_type": fake_data.link_type_kobo.pk,
                                    }
                                ],
                                "narrators": [str(fake_data.person_bela.uuid)],
                                "paid": True,
                                "preview_url": "https://youtube.com/",
                                "publishers": [str(publisher.uuid)],
                                "translators": [str(fake_data.person_viktar.uuid)],
                                "uuid": str(book.narrations.first().uuid),
                            }
                        ],
                        "slug": "book-1",
                        "tag": [fake_data.tag_classics.pk],
                        "title": "Book 1",
                        "uuid": str(book.uuid),
                    }
                ],
                "link_types": [
                    {
                        "availability": "EVERYWHERE",
                        "caption": "Кніжны Воз",
                        "icon": fake_data.link_type_knizhny_voz.icon.url,
                        "id": fake_data.link_type_knizhny_voz.pk,
                        "name": "knizny_voz",
                    },
                    {
                        "availability": "EVERYWHERE",
                        "caption": "Kobo",
                        "icon": fake_data.link_type_kobo.icon.url,
                        "id": fake_data.link_type_kobo.pk,
                        "name": "kobo",
                    },
                ],
                "people": [
                    {
                        "description": "Ales description",
                        "description_source": "",
                        "gender": "MALE",
                        "name": "Алесь Алесявіч",
                        "photo": None,
                        "photo_source": "",
                        "slug": "ales-alesievich",
                        "uuid": str(fake_data.person_ales.uuid),
                    },
                    {
                        "description": "",
                        "description_source": "",
                        "gender": "FEMALE",
                        "name": "Бэла Бэлаўна",
                        "photo": None,
                        "photo_source": "",
                        "slug": "bela-belawna",
                        "uuid": str(fake_data.person_bela.uuid),
                    },
                    {
                        "description": "",
                        "description_source": "",
                        "gender": "MALE",
                        "name": "Віктар Віктаравіч",
                        "photo": None,
                        "photo_source": "",
                        "slug": "viktar-viktavarich",
                        "uuid": str(fake_data.person_viktar.uuid),
                    },
                    {
                        "description": "",
                        "description_source": "",
                        "gender": "FEMALE",
                        "name": "Вольга Янаўна",
                        "photo": None,
                        "photo_source": "",
                        "slug": "volha-yanayna",
                        "uuid": str(fake_data.person_volha.uuid),
                    },
                ],
                "publishers": [
                    {
                        "description": "Мы - каманда энтузіястаў.",
                        "logo": publisher.logo.url,
                        "name": "audiobooks.by",
                        "slug": "audiobooksby",
                        "url": "https://audiobooks.by/about",
                        "uuid": str(publisher.uuid),
                    }
                ],
                "tags": [
                    {
                        "description": "",
                        "id": fake_data.tag_classics.pk,
                        "name": "Класікі беларускай літаратуры",
                        "slug": "classics",
                    },
                    {
                        "description": "",
                        "id": fake_data.tag_contemporary.pk,
                        "name": "Сучасная проза",
                        "slug": "contemporary",
                    },
                    {
                        "description": "",
                        "id": fake_data.tag_read_by_author.pk,
                        "name": "чытае аўтар",
                        "slug": "cytaje-autar",
                    },
                ],
            },
            response.json(),
        )
