import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from selenium import webdriver
from books import models


class PersonPageTests(StaticLiveServerTestCase):
    '''Selenium tests for person page.'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)

    def setUp(self):
        call_command('loaddata', 'data/data.json')
        self.person = models.Person.objects.filter(
            name='Андрэй Хадановіч').first()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def _get_person_url(self) -> str:
        return f'{self.live_server_url}/person/{self.person.slug}'

    def _check_book_present(self, book: models.Book) -> None:
        found = False
        for elem in self.driver.find_elements_by_link_text(book.title):
            found = found or elem.get_dom_attribute(
                'href') == f'/books/{book.slug}'
        self.assertTrue(
            found, f'Did not find link for book {book.title} {book.slug}')

    def test_books_authored(self):
        self.driver.get(self._get_person_url())
        self.assertGreaterEqual(self.person.books_authored.count(), 1)
        for book in self.person.books_authored.all():
            self._check_book_present(book)

    def test_books_translated(self):
        self.driver.get(self._get_person_url())
        self.assertGreaterEqual(self.person.books_translated.count(), 1)
        for book in self.person.books_translated.all():
            self._check_book_present(book)

    def test_books_narrated(self):
        self.driver.get(self._get_person_url())
        self.assertGreaterEqual(self.person.narrations.count(), 1)
        for narration in self.person.narrations.all():
            self._check_book_present(narration.book)