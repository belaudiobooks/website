from datetime import date
from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class PersonPageTests(WebdriverTestCase):
    '''Selenium tests for person page.'''

    def setUp(self):
        super().setUp()
        self.person = self.fake_data.person_ales

    def _get_person_url(self) -> str:
        return f'{self.live_server_url}/person/{self.person.slug}'

    def _check_books_present(self, section_name: str, books: list[models.Book]):
        section = self.driver.find_element(By.CSS_SELECTOR, f'[data-test="{section_name}"]')
        self.assertGreater(len(books), 0)
        for book in books:
            books_links = section.find_elements(By.LINK_TEXT, book.title)
            self.assertEquals(
                1, len(books_links), f'Book "{book.title}" not found or found more than once')
            self.assertEquals(f'/books/{book.slug}', books_links[0].get_dom_attribute('href'))

    def test_shows_correct_books(self):
        book_authored_1 = self.fake_data.create_book_with_single_narration(
            title='Book 1',
            authors=[self.person],
        )
        book_authored_2 = self.fake_data.create_book_with_single_narration(
            title='Book 2',
            authors=[self.person, self.fake_data.person_bela],
        )

        book_translated_1 = self.fake_data.create_book_with_single_narration(
                title='Book 3',
                translators=[self.person],
        )
        book_translated_2 = self.fake_data.create_book_with_single_narration(
                title='Book 4',
        )
        book_translated_2.narrations.first().translators.add(self.person)

        book_narrated = self.fake_data.create_book_with_single_narration(
                title='Book 5',
                narrators=[self.person],
        )
        nar2 = book_narrated.narrations.create(date = date.today())
        nar2.narrators.add(self.person)
        nar2.save()

        self.driver.get(self._get_person_url())
        self._check_books_present('books-authored', [book_authored_1, book_authored_2])
        self._check_books_present('books-translated', [book_translated_1, book_translated_2])
        self._check_books_present('books-narrated', [book_narrated])

    def test_page_elements(self):
        self.driver.get(self._get_person_url())
        self.assertEqual(f'{self.person.name}, аўдыякнігі', self.driver.title)
        description = self.driver.find_element(
            By.CSS_SELECTOR,
            'meta[name="description"]').get_dom_attribute('content')
        self.assertIn(self.person.name, description)

    def test_photo_source_rendered_correctly(self):
        self.person.photo = self.fake_data.create_image()
        self.person.save()

        # No citation should be rendered by default, when photo_source is not set.
        self.driver.get(self._get_person_url())
        self.assertEquals(0, self.count_elements('[data-test="bio"] .citation'))

        self.person.photo_source = 'YouTube;https://www.youtube.com/watch?v=123'
        self.person.save()

        self.driver.get(self._get_person_url())
        self.assertEquals(1, self.count_elements('[data-test="bio"] .citation'))
        source_element = self.driver.find_element(
            By.CSS_SELECTOR, '[data-test="bio"] .citation')
        self.assertEquals('Крыніца: YouTube', source_element.text)
        self.assertEquals(
            'https://www.youtube.com/watch?v=123',
            source_element.find_element(By.CSS_SELECTOR, 'a').get_dom_attribute('href'))
