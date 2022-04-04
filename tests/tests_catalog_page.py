from typing import List
from books import models
from books.views import BOOKS_PER_PAGE
from tests.webdriver_test_case import WebdriverTestCase


class CatalogPageTests(WebdriverTestCase):
    '''Selenium tests for catalog page.'''

    def _assert_page_contains_books(self, books: List[models.Book]) -> None:
        for book in books:
            self.assertIsNotNone(
                self.driver.find_element_by_link_text(book.title))

    def _test_pagination(self, books: List[models.Book]) -> None:
        self._assert_page_contains_books(books[:BOOKS_PER_PAGE])

        # Go to next page.
        self.scroll_and_click(
            self.driver.find_element_by_css_selector('.next-page'))
        self._assert_page_contains_books(books[BOOKS_PER_PAGE:BOOKS_PER_PAGE *
                                               2])

        # Go to the last page.
        self.scroll_and_click(
            self.driver.find_element_by_css_selector('.last-page'))
        last_page_book_start = int(
            len(books) / BOOKS_PER_PAGE * BOOKS_PER_PAGE)
        self._assert_page_contains_books(books[last_page_book_start:])

        # Go to the page before last.
        self.scroll_and_click(
            self.driver.find_element_by_css_selector('.prev-page'))
        self._assert_page_contains_books(books[last_page_book_start -
                                               BOOKS_PER_PAGE:BOOKS_PER_PAGE])

        # Go to the first page.
        self.scroll_and_click(
            self.driver.find_element_by_css_selector('.first-page'))
        self._assert_page_contains_books(books[0:BOOKS_PER_PAGE])

    def test_all_books(self):
        self.driver.get(f'{self.live_server_url}/catalog')
        self.assertEqual('Усе аўдыякнігі', self.driver.title)
        books = list(
            models.Book.objects.filter(
                status=models.BookStatus.ACTIVE).order_by('-added_at'))
        self._test_pagination(books)

    def test_genre_page(self):
        tag = models.Tag.objects.filter(name='Сучасная проза').first()
        self.driver.get(f'{self.live_server_url}/catalog/{tag.slug}')
        self.assertEqual(tag.name, self.driver.title)
        books = list(
            models.Book.objects.filter(
                tag=tag.id,
                status=models.BookStatus.ACTIVE).order_by('-added_at'))
        self._test_pagination(books)