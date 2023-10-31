from datetime import date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class BookPageTests(WebdriverTestCase):
    '''Selenium tests for book page.'''

    def setUp(self):
        super().setUp()
        self.book = self.fake_data.create_book_with_single_narration(
            title='Першая кніга',
            authors=[self.fake_data.person_ales],
            translators=[self.fake_data.person_bela],
            narrators=[self.fake_data.person_viktar],
            link_types=[
                self.fake_data.link_type_knizhny_voz,
                self.fake_data.link_type_kobo
            ],
            tags=[self.fake_data.tag_poetry, self.fake_data.tag_fiction],
            publishers=[self.fake_data.publisher_audiobooksby],
            duration=timedelta(hours=14, minutes=15),
            livelib_url='https://www.livelib.ru/book/pershaya-kniga')

    def _get_book_url(self) -> str:
        return f'{self.live_server_url}/books/{self.book.slug}'

    def _check_person_present_and_clickable(self,
                                            person: models.Person) -> None:
        self.driver.get(self._get_book_url())
        elem = self.driver.find_element(By.LINK_TEXT, person.name)
        self.scroll_and_click(elem)
        self.assertIn(f'/person/{person.slug}', self.driver.current_url)

    def test_click_authors(self):
        self.assertGreaterEqual(self.book.authors.count(), 1)
        for author in self.book.authors.all():
            self._check_person_present_and_clickable(author)

    def test_click_translators(self):
        self.assertGreaterEqual(self.book.translators.count(), 1)
        for translator in self.book.translators.all():
            self._check_person_present_and_clickable(translator)

    def test_click_narrators(self):
        self.assertGreaterEqual(self.book.narrations.count(), 1)
        for narration in self.book.narrations.all():
            for narrator in narration.narrators.all():
                self._check_person_present_and_clickable(narrator)

    def test_has_narration_links(self):
        self.assertGreaterEqual(self.book.narrations.count(), 1)
        self.driver.get(self._get_book_url())
        for narration in self.book.narrations.all():
            for link in narration.links.all():
                caption = link.url_type.caption
                elem = self.driver.find_elements(By.LINK_TEXT, caption)
                found_link = False
                for e in elem:
                    if e.get_dom_attribute('href') == link.url:
                        found_link = True
                        break
                self.assertTrue(found_link)

    def test_click_tags(self):
        self.assertGreaterEqual(self.book.tag.count(), 1)
        for tag in self.book.tag.all():
            self.driver.get(self._get_book_url())
            elem = self.driver.find_element(By.LINK_TEXT, tag.name)
            self.scroll_and_click(elem)
            self.assertIn(f'/catalog/{tag.slug}', self.driver.current_url)
            tag_header = self.driver.find_element(By.CSS_SELECTOR, '#books h1')
            self.assertEqual(tag.name, tag_header.text)

    def test_renders_text_elements(self):
        self.driver.get(self._get_book_url())
        book_elem = self.driver.find_element(By.CSS_SELECTOR, '#books')
        self.assertIn('14 гадзін 15 хвілін', book_elem.text)
        self.assertEqual(f'Першая Кніга аўдыякніга', self.driver.title)
        description = self.driver.find_element(
            By.CSS_SELECTOR,
            'meta[name="description"]').get_dom_attribute('content')
        self.assertIn(self.book.title, description)
        self.assertIn(self.book.authors.first().name, description)

    def test_free_books_have_listen_free_text(self):
        self.driver.get(self._get_book_url())
        header = self.driver.find_element(By.CSS_SELECTOR, '.links-header')
        self.assertIn('Дзе паслухаць бясплатна', header.text)

    def test_paid_books_have_where_to_buy_text(self):
        narration = self.book.narrations.first()
        narration.paid = True
        narration.save()
        self.driver.get(self._get_book_url())
        header = self.driver.find_element(By.CSS_SELECTOR, '.links-header')
        self.assertIn('Дзе купіць', header.text)

    def test_russian_only_books_show_both_titles(self):
        self.book.title = 'Першая кніга'
        self.book.title_ru = 'Первая книга'
        self.book.save()
        narration = self.book.narrations.first()
        narration.language = models.Language.RUSSIAN
        narration.save()
        self.driver.get(self._get_book_url())
        body_text = self.driver.find_element(By.CSS_SELECTOR, '#books').text
        self.assertIn('Першая кніга', body_text)
        self.assertIn('Первая книга', body_text)

    def test_has_publisher_clickable_link(self):
        self.driver.get(self._get_book_url())
        publisher = models.Publisher.objects.filter(
            name="audiobooks.by").first()
        elem = self.driver.find_element(By.LINK_TEXT, f"{publisher.name}")
        self.scroll_and_click(elem)
        self.assertIn(f'/publisher/{publisher.slug}', self.driver.current_url)

    def test_has_livelib_clickable_link(self):
        self.driver.get(self._get_book_url())
        elem = self.driver.find_element(By.LINK_TEXT, "LiveLib")
        self.assertEqual('https://www.livelib.ru/book/pershaya-kniga',
                         elem.get_attribute("href"))

    def _create_narration(self, language: models.Language,
                          number_of_links: int,
                          narrator: models.Person) -> models.Narration:
        narration = models.Narration(language=language,
                                     book=self.book,
                                     paid=False)
        narration.save()
        for i in range(number_of_links):
            narration.links.add(
                models.Link.objects.create(
                    url=f'https://example.com/{self.book.slug}_{narrator.slug}',
                    url_type=self.fake_data.link_type_kobo,
                ))
        narration.narrators.set([narrator])
        return narration

    def test_multiple_narrations_ordered_correctly(self):
        # Book has 3 narrations.
        # Narration 1: RU, 2 links
        # Narration 2: BY, 0 links
        # Narration 3: BY, 1 link
        # Expected order is: 3, 2, 1.
        self.book.narrations.all().delete()
        self.book.narrations.set([
            self._create_narration(models.Language.RUSSIAN, 2,
                                   self.fake_data.person_ales),
            self._create_narration(models.Language.BELARUSIAN, 0,
                                   self.fake_data.person_bela),
            self._create_narration(models.Language.BELARUSIAN, 1,
                                   self.fake_data.person_viktar),
        ])
        self.driver.get(self._get_book_url())
        narrators_sections = self.driver.find_elements(
            By.CSS_SELECTOR, '[data-test="narrators"]')
        self.assertEqual(3, len(narrators_sections))
        self.assertIn(self.fake_data.person_viktar.name,
                      narrators_sections[0].text)
        self.assertIn(self.fake_data.person_bela.name,
                      narrators_sections[1].text)
        self.assertIn(self.fake_data.person_ales.name,
                      narrators_sections[2].text)

    def test_book_description_merged_with_narration_when_single_narration(
            self):
        self.book.description = 'Book description'
        self.book.save()
        narration = self.book.narrations.first()
        narration.description = 'Narration description'
        narration.save()

        self.driver.get(self._get_book_url())

        description = self.driver.find_element(
            By.CSS_SELECTOR, '[data-test="book-description"]').text
        self.assertIn(self.book.description, description)
        self.assertIn(narration.description, description)

    def test_book_description_separate_from_narration_when_multiple(self):
        self.book.description = 'Book description'
        self.book.save()
        narration1 = self.book.narrations.first()
        narration1.description = 'Narration one description'
        narration1.save()
        narration2 = models.Narration.objects.create(
            book=self.book,
            language=models.Language.BELARUSIAN,
            paid=False,
            description='Narration two description',
        )

        self.driver.get(self._get_book_url())

        description = self.driver.find_element(
            By.CSS_SELECTOR, '[data-test="book-description"]').text
        self.assertIn(self.book.description, description)
        self.assertNotIn(narration1.description, description)
        self.assertNotIn(narration2.description, description)

        narration_descriptions = self.driver.find_elements(
            By.CSS_SELECTOR, '[data-test="narration-description"]')
        self.assertEqual(2, len(narration_descriptions))
        self.assertIn(narration1.description, narration_descriptions[0].text)
        self.assertIn(narration2.description, narration_descriptions[1].text)

    def test_covers_rendered_correctly(self):
        self.driver.get(self._get_book_url())

        # When book has a single narration - only book cover is displayed.
        self.assertEquals(
            1, self.count_elements('[data-test="book-cover"] .photo'))
        self.assertEquals(
            0, self.count_elements('[data-test="narration-cover"] .photo'))

        # When a book has two or more narrations - we display covers per narration.
        narration2 = models.Narration.objects.create(
            book=self.book,
            language=models.Language.BELARUSIAN,
            paid=False,
        )
        self.driver.get(self._get_book_url())

        self.assertEquals(
            0, self.count_elements('[data-test="book-cover"] .photo'))
        self.assertEquals(
            2, self.count_elements('[data-test="narration-cover"] .photo'))
