from datetime import date, timedelta
from typing import Union
from collections.abc import Sequence
from selenium.webdriver.remote.webelement import WebElement
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
            tags=[self.fake_data.tag_classics, self.fake_data.tag_classics],
            publishers=[self.fake_data.publisher_audiobooksby],
            duration=timedelta(hours=14, minutes=15),
            livelib_url='https://www.livelib.ru/book/pershaya-kniga')

    def _get_section(self, book_or_narration: Union[models.Book, models.Narration]) -> WebElement:
        if isinstance(book_or_narration, models.Book):
            return self.driver.find_element(By.CSS_SELECTOR, '[data-test="book-section"]')
        else:
            selector = f'[data-test="narration-section"][data-narration-id="{book_or_narration.uuid}"]'
            return self.driver.find_element(By.CSS_SELECTOR, selector)

    def _get_book_url(self) -> str:
        return f'{self.live_server_url}/books/{self.book.slug}'

    def _check_persons_present_and_clickable(self,
                                            expected_section: Union[models.Book, models.Narration],
                                            persons: Sequence[models.Person]) -> None:
        section = self._get_section(expected_section)
        self.assertGreaterEqual(len(persons), 1)
        for person in persons:
            elem = section.find_element(By.LINK_TEXT, person.name)
            self.assertEquals(f'/person/{person.slug}', elem.get_dom_attribute('href'))

    def _check_narration_links_present(self, expected_section: Union[models.Book, models.Narration],
                                       narration: models.Narration):
        section = self._get_section(expected_section)
        for link in narration.links.all():
            caption = link.url_type.caption
            elem = section.find_element(By.LINK_TEXT, caption)
            self.assertEquals(link.url, elem.get_dom_attribute('href'))

    def _create_narration(self, language: models.Language,
                          narrator: models.Person,
                          date: date=date.today()) -> models.Narration:
        narration = models.Narration(language=language,
                                     book=self.book,
                                     paid=False,
                                     date=date)
        narration.save()
        narration.links.add(
            models.Link.objects.create(
                url=f'https://example.com/{self.book.slug}_{narrator.slug}',
                url_type=self.fake_data.link_type_kobo,
            ))
        narration.narrators.set([narrator])
        return narration

    def test_elements_rendered_in_book_section_with_single_narration(self):
        self.driver.get(self._get_book_url())
        narration = self.book.narrations.first()
        self._check_persons_present_and_clickable(self.book, self.book.authors.all())
        self._check_persons_present_and_clickable(self.book, narration.translators.all())
        self._check_persons_present_and_clickable(self.book, narration.narrators.all())
        self._check_narration_links_present(narration, narration)

    def test_elements_rendered_per_narration_with_multiple_narrations(self):
        nar1 = self.book.narrations.first()

        nar2_narrator = models.Person.objects.create(
            name='Nar 2',
            name_ru='Nar 2',
            slug='nar-2',
        )
        nar2_translator = models.Person.objects.create(
            name='Tran 2',
            name_ru='Tran 2',
            slug='tran-2',
        )
        nar2 = self._create_narration(
            language=models.Language.BELARUSIAN,
            narrator=nar2_narrator
        )
        nar2.translators.set([nar2_translator])
        nar2.save()

        self.driver.get(self._get_book_url())

        self._check_persons_present_and_clickable(self.book, self.book.authors.all())

        # Verify that narrators, translators and links rendered in first narration section.
        self._check_persons_present_and_clickable(nar1, nar1.narrators.all())
        self._check_persons_present_and_clickable(nar1, nar1.translators.all())
        self._check_narration_links_present(nar1, nar1)

        # Verify that narrators, translators and links rendered in second narration section.
        self._check_persons_present_and_clickable(nar2, nar2.narrators.all())
        self._check_persons_present_and_clickable(nar2, nar2.translators.all())
        self._check_narration_links_present(nar2, nar2)

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

    def test_multiple_narrations_ordered_correctly(self):
        # Book has 3 narrations.
        # Narration 1: RU, Jan 3
        # Narration 2: BY, Jan 1
        # Narration 3: BY, Jan 2
        # Expected order is: 3, 2, 1.
        self.book.narrations.all().delete()
        self.book.narrations.set([
            self._create_narration(models.Language.RUSSIAN,
                                   self.fake_data.person_ales,
                                   date=date(2020, 1, 3)),
            self._create_narration(models.Language.BELARUSIAN,
                                   self.fake_data.person_bela,
                                   date=date(2020, 1, 1)),
            self._create_narration(models.Language.BELARUSIAN,
                                   self.fake_data.person_viktar,
                                   date=date(2020, 1, 2)),
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
            date=date.today(),
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
            1, self.count_elements('[data-test="book-cover"] .cover-large'))
        self.assertEquals(
            0, self.count_elements('[data-test="narration-cover"] .cover-large'))

        # When a book has two or more narrations - we display covers per narration.
        narration2 = models.Narration.objects.create(
            book=self.book,
            language=models.Language.BELARUSIAN,
            paid=False,
            date=date.today(),
        )
        self.driver.get(self._get_book_url())

        self.assertEquals(
            0, self.count_elements('[data-test="book-cover"] .cover-large'))
        self.assertEquals(
            2, self.count_elements('[data-test="narration-cover"] .cover-large'))

    def test_cover_source_rendered_correctly(self):
        narration = self.book.narrations.first()
        narration.cover_image = self.fake_data.create_image()
        narration.save()

        # No citation should be rendered by default, when cover_image_source is not set.
        self.driver.get(self._get_book_url())
        self.assertEquals(0, self.count_elements('[data-test="book-cover"] .citation'))

        narration.cover_image_source = 'YouTube;https://www.youtube.com/watch?v=123'
        narration.save()

        self.driver.get(self._get_book_url())
        self.assertEquals(1, self.count_elements('[data-test="book-cover"] .citation'))
        source_element = self.driver.find_element(
            By.CSS_SELECTOR, '[data-test="book-cover"] .citation')
        self.assertEquals('Крыніца: YouTube', source_element.text)
        self.assertEquals(
            'https://www.youtube.com/watch?v=123',
            source_element.find_element(By.CSS_SELECTOR, 'a').get_dom_attribute('href'))

    def test_invalid_cover_source_doesnt_crash_site(self):
        narration = self.book.narrations.first()
        narration.cover_image = self.fake_data.create_image()
        # Source uses semicolon instead of comma.
        narration.cover_image_source = 'YouTube,https://www.youtube.com/watch?v=123'
        narration.save()

        # No citation should be rendered by default, when cover_image_source is not set.
        self.driver.get(self._get_book_url())
        self.assertEquals(0, self.count_elements('[data-test="book-cover"] .citation'))

    def test_slug_generation(self):
        book1 = models.Book.objects.create(
            title='Казкі',
        )
        self.assertEquals('kazki', book1.slug)

        # test for a bug when saving again might detect a slug conflict coming from the
        # book itself
        book1.save()
        self.assertEquals('kazki', book1.slug)

        book2 = models.Book.objects.create(
            title='Казкі',
        )
        self.assertEquals('kazki-2', book2.slug)
        book3 = models.Book.objects.create(
            title='Казкі',
        )
        self.assertEquals('kazki-3', book3.slug)
