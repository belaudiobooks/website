from typing import List
from books import models
from books.views import BOOKS_PER_PAGE
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from urllib.parse import urlparse


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

    def _get_all_books_on_page(self) -> List[models.Book]:
        slugs = []
        for book in self.driver.find_elements(By.CSS_SELECTOR,
                                              '[data-type="book-title"]'):
            link = urlparse(book.get_attribute('href'))
            # Slug is the last part of the url.
            slugs.append(link.path.split('/')[-1])
        books = models.Book.objects.filter(slug__in=slugs)
        self.assertEqual(len(slugs), len(books))
        return books

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

    def test_russian_language_filter(self):
        self.driver.get(f'{self.live_server_url}/catalog')
        filter = Select(
            self.driver.find_element(By.CSS_SELECTOR, '#filter-language'))
        self.assertListEqual([o.text for o in filter.options],
                             ['любая', 'беларуская', 'руская'])
        filter.select_by_visible_text('руская')
        books = self._get_all_books_on_page()
        self.assertGreater(len(books), 0)
        for book in books:
            self.assertGreater(
                book.narrations.filter(language='RUSSIAN').count(), 0,
                f'Book {book.title} has no russian narrations')

    def test_price_filter_paid(self):
        self.driver.get(f'{self.live_server_url}/catalog')
        filter = Select(
            self.driver.find_element(By.CSS_SELECTOR, '#filter-price'))
        self.assertListEqual([o.text for o in filter.options],
                             ['усе', 'платныя', 'бясплатныя'])
        filter.select_by_visible_text('платныя')
        books = self._get_all_books_on_page()
        self.assertGreater(len(books), 0)
        for book in books:
            self.assertGreater(
                book.narrations.filter(paid=True).count(), 0,
                f'Book {book.title} has no paid narrations')

        # Check that filter remains after going to the next page.
        self.scroll_and_click(
            self.driver.find_element(By.LINK_TEXT, 'Сучасная проза'))
        books = self._get_all_books_on_page()
        self.assertGreater(len(books), 0)
        for book in books:
            self.assertIn('Сучасная проза',
                          [tag.name for tag in book.tag.all()],
                          f'Book {book.title} has no tag Сучасная проза')
            self.assertGreater(
                book.narrations.filter(paid=True).count(), 0,
                f'Book {book.title} has no paid narrations')

    def test_price_filter_free(self):
        self.driver.get(f'{self.live_server_url}/catalog')
        filter = Select(
            self.driver.find_element(By.CSS_SELECTOR, '#filter-price'))
        filter.select_by_visible_text('бясплатныя')
        books = self._get_all_books_on_page()
        self.assertGreater(len(books), 0)
        for book in books:
            self.assertGreater(
                book.narrations.filter(paid=False).count(), 0,
                f'Book {book.title} has no free narrations')
