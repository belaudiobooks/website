from typing import List
from books import models
from books.views import BOOKS_PER_PAGE
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class CatalogPageTests(WebdriverTestCase):
    '''Selenium tests for catalog page.'''

    def _assert_page_contains_books(self, books: List[models.Book]) -> None:
        for book in books:
            self.assertIsNotNone(
                self.driver.find_element(By.LINK_TEXT, book.title))

    def _test_pagination(self, books: List[models.Book]) -> None:
        self._assert_page_contains_books(books[:BOOKS_PER_PAGE])

        # Go to next page.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.next-page'))
        self._assert_page_contains_books(books[BOOKS_PER_PAGE:BOOKS_PER_PAGE *
                                               2])

        # Go to the last page.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.last-page'))
        last_page_book_start = int(
            len(books) / BOOKS_PER_PAGE * BOOKS_PER_PAGE)
        self._assert_page_contains_books(books[last_page_book_start:])

        # Go to the page before last.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.prev-page'))
        self._assert_page_contains_books(books[last_page_book_start -
                                               BOOKS_PER_PAGE:BOOKS_PER_PAGE])

        # Go to the first page.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.first-page'))
        self._assert_page_contains_books(books[0:BOOKS_PER_PAGE])

    def test_all_books(self):
        self.driver.get(f'{self.live_server_url}/catalog')
        self.assertEqual('Усе аўдыякнігі', self.driver.title)
        books = list(
            models.Book.objects.filter(
                status=models.BookStatus.ACTIVE).order_by('-date'))
        self._test_pagination(books)

    def test_all_books_with_link_filter(self):
        link_type = models.LinkType.objects.get(name='knihi_com')
        self.driver.get(
            f'{self.live_server_url}/catalog?links={link_type.name}')
        self.assert_page_contains_only_books_of_link_type(link_type)

        # Go to next page and make sure that filter remains.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.next-page'))
        self.assert_page_contains_only_books_of_link_type(link_type)
        self.assertIn(f'links={link_type.name}', self.driver.current_url)

    def test_genre_page(self):
        tag = models.Tag.objects.filter(name='Сучасная проза').first()
        self.driver.get(f'{self.live_server_url}/catalog/{tag.slug}')
        self.assertEqual(tag.name, self.driver.title)
        books = list(
            models.Book.objects.filter(
                tag=tag.id, status=models.BookStatus.ACTIVE).order_by('-date'))
        self._test_pagination(books)

    def test_read_by_author_genre(self):
        self.driver.get(f'{self.live_server_url}/update_read_by_author_tag')
        tag = models.Tag.objects.filter(
            name='Чытае аўтар').prefetch_related('books').first()
        self.assertGreater(len(tag.books.all()), 10)
        for book in tag.books.all()[:10]:
            read_by_author = False
            authors = set(book.authors.all())
            for narration in book.narrations.all():
                for narrator in narration.narrators.all():
                    if narrator in authors:
                        read_by_author = True
            self.assertTrue(read_by_author)

    def test_genre_page_with_link_filter(self):
        tag = models.Tag.objects.filter(name='Сучасная проза').first()
        link_type = models.LinkType.objects.get(name='knihi_com')
        self.driver.get(
            f'{self.live_server_url}/catalog/{tag.slug}?links={link_type.name}'
        )
        self.assert_page_contains_only_books_of_link_type(link_type)

        # Go to next page and make sure that filter remains.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.next-page'))
        self.assert_page_contains_only_books_of_link_type(link_type)
        self.assertIn(f'links={link_type.name}', self.driver.current_url)