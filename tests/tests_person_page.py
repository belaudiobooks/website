from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class PersonPageTests(WebdriverTestCase):
    '''Selenium tests for person page.'''

    # TODO: #90 - remove once all tests switch to using fake data.
    fixtures = []

    def setUp(self):
        super().setUp()
        self.person = self.fake_data.person_ales
        self.books_authored = [
            self.fake_data.create_book_with_single_narration(
                title='Book 1',
                authors=[self.person],
            ),
            self.fake_data.create_book_with_single_narration(
                title='Book 2',
                authors=[self.person, self.fake_data.person_bela],
            ),
        ]
        self.books_translated = [
            self.fake_data.create_book_with_single_narration(
                title='Book 3',
                translators=[self.person],
            ),
        ]
        self.books_narrated = [
            self.fake_data.create_book_with_single_narration(
                title='Book 4',
                narrators=[self.person],
            ),
        ]

    def _get_person_url(self) -> str:
        return f'{self.live_server_url}/person/{self.person.slug}'

    def _check_book_present(self, book: models.Book) -> None:
        found = False
        for elem in self.driver.find_elements(By.LINK_TEXT, book.title):
            found = found or elem.get_dom_attribute(
                'href') == f'/books/{book.slug}'
        self.assertTrue(
            found, f'Did not find link for book {book.title} {book.slug}')

    def test_books_authored(self):
        self.driver.get(self._get_person_url())
        for book in self.books_authored:
            self._check_book_present(book)

    def test_books_translated(self):
        self.driver.get(self._get_person_url())
        for book in self.books_translated:
            self._check_book_present(book)

    def test_books_narrated(self):
        self.driver.get(self._get_person_url())
        for book in self.books_narrated:
            self._check_book_present(book)

    def test_page_elements(self):
        self.driver.get(self._get_person_url())
        self.assertEqual(f'{self.person.name}, аўдыякнігі', self.driver.title)
        description = self.driver.find_element(
            By.CSS_SELECTOR,
            'meta[name="description"]').get_dom_attribute('content')
        self.assertIn(self.person.name, description)
