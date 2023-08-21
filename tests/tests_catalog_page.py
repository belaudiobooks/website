from datetime import date, timedelta
from typing import List, Set
from books import models
from books.views.catalog import BOOKS_PER_PAGE
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from urllib.parse import urlparse


class CatalogPageTests(WebdriverTestCase):
    '''Selenium tests for catalog page.'''

    def _assert_page_contains_books(self, books: List[models.Book]) -> None:
        titles = self._get_all_books_on_page()
        for book in books:
            self.assertIn(book.title, titles)

    def _assert_page_does_not_contain_books(self,
                                            books: List[models.Book]) -> None:
        titles = self._get_all_books_on_page()
        for book in books:
            self.assertNotIn(book.title, titles)

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

    def _get_all_books_on_page(self) -> Set[str]:
        return set([
            el.text for el in self.driver.find_elements(
                By.CSS_SELECTOR, '[data-test="book-title"]')
        ])

    def _last_n_days(self, n: int) -> List[date]:
        next_date = date.today()
        res = []
        for i in range(n):
            res.append(next_date)
            next_date = next_date - timedelta(days=1)
        return res

    def _choose_filter(self, filter_id: str, filter_value: str) -> None:
        filter = Select(self.driver.find_element(By.CSS_SELECTOR, filter_id))
        filter.select_by_visible_text(filter_value)

    def test_all_books(self):
        for i, d in enumerate(self._last_n_days(5 * BOOKS_PER_PAGE)):
            self.fake_data.create_book_with_single_narration(
                title=f'Кніга {i}',
                date=d,
            )
        self.driver.get(f'{self.live_server_url}/catalog')
        self.assertEqual('Усе аўдыякнігі', self.driver.title)
        books = list(
            models.Book.objects.filter(
                status=models.BookStatus.ACTIVE).order_by('-date'))
        self._test_pagination(books)

    def test_all_books_with_link_filter(self):
        books_kobo = []
        books_knizhny_voz = []
        for i, d in enumerate(self._last_n_days(2 * BOOKS_PER_PAGE)):
            books_kobo.append(
                self.fake_data.create_book_with_single_narration(
                    f'Kobo book {i}',
                    link_types=[self.fake_data.link_type_kobo],
                    date=d,
                    tags=[self.fake_data.tag_poetry],
                ))
            books_knizhny_voz.append(
                self.fake_data.create_book_with_single_narration(
                    f'Knizhny voz book {i}',
                    link_types=[self.fake_data.link_type_knizhny_voz],
                    date=d,
                    tags=[self.fake_data.tag_poetry],
                ))

        self.driver.get(f'{self.live_server_url}/catalog')
        # Initially first page contains half of books of each type.
        self._assert_page_contains_books(books_kobo[:BOOKS_PER_PAGE // 2])
        self._assert_page_contains_books(books_knizhny_voz[:BOOKS_PER_PAGE //
                                                           2])
        self._choose_filter('#filter-links',
                            self.fake_data.link_type_kobo.caption)

        self._assert_page_contains_books(books_kobo[:BOOKS_PER_PAGE])
        self._assert_page_does_not_contain_books(books_knizhny_voz)

        # Go to next page and make sure that filter remains.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.next-page'))
        self._assert_page_contains_books(books_kobo[BOOKS_PER_PAGE:])

        # Go to genre page and make sure that filter remains.
        self.driver.find_element(By.LINK_TEXT,
                                 self.fake_data.tag_poetry.name).click()
        self._assert_page_contains_books(books_kobo[:BOOKS_PER_PAGE])

    def test_all_books_with_custom_limit(self):
        for i, d in enumerate(self._last_n_days(100)):
            self.fake_data.create_book_with_single_narration(
                f'Кніга {i}',
                date=d,
            )
        self.driver.get(f'{self.live_server_url}/catalog?limit=50')
        self.assertEqual(len(self._get_all_books_on_page()), 50)
        # Go to next page and make sure that limit remains.
        self.scroll_and_click(
            self.driver.find_element(By.CSS_SELECTOR, '.next-page'))
        self.assertEqual(len(self._get_all_books_on_page()), 50)

    def test_genre_page(self):
        books_poetry = []
        books_fiction = []
        for i, d in enumerate(self._last_n_days(3 * BOOKS_PER_PAGE)):
            books_poetry.append(
                self.fake_data.create_book_with_single_narration(
                    f'Паэзія {i}',
                    date=d,
                    tags=[self.fake_data.tag_poetry],
                ))
            books_fiction.append(
                self.fake_data.create_book_with_single_narration(
                    f'Мастацкая {i}',
                    date=d,
                    tags=[self.fake_data.tag_fiction],
                ))
        self.driver.get(f'{self.live_server_url}/catalog')
        self.driver.find_element(By.LINK_TEXT,
                                 self.fake_data.tag_poetry.name).click()
        self.assertEqual(self.fake_data.tag_poetry.name, self.driver.title)
        self._test_pagination(books_poetry)

    def test_read_by_author_genre(self):
        book_read_by_author = self.fake_data.create_book_with_single_narration(
            title='By author',
            authors=[self.fake_data.person_ales],
            narrators=[self.fake_data.person_ales, self.fake_data.person_bela],
        )
        book_read_by_someone_else = self.fake_data.create_book_with_single_narration(
            title='By someone else',
            narrators=[self.fake_data.person_bela],
        )
        self.driver.get(
            f'{self.live_server_url}/job/update_read_by_author_tag')
        self.driver.get(f'{self.live_server_url}/catalog')
        self.driver.find_element(
            By.LINK_TEXT, self.fake_data.tag_read_by_author.name).click()
        self._assert_page_contains_books([book_read_by_author])
        self._assert_page_does_not_contain_books([book_read_by_someone_else])

    def test_language_filter(self):
        book_belarusian = self.fake_data.create_book_with_single_narration(
            title='Belarusian',
            tags=[self.fake_data.tag_poetry],
            language=models.Language.BELARUSIAN,
        )
        book_russian = self.fake_data.create_book_with_single_narration(
            title='Russian',
            tags=[self.fake_data.tag_poetry],
            language=models.Language.RUSSIAN,
        )
        book_both_languages = self.fake_data.create_book_with_single_narration(
            title='Both',
            language=models.Language.BELARUSIAN,
        )
        models.Narration.objects.create(
            book=book_both_languages,
            language=models.Language.RUSSIAN,
            duration=timedelta(minutes=15),
        )
        self.driver.get(f'{self.live_server_url}/catalog')

        self._choose_filter('#filter-language', 'беларуская')
        self._assert_page_contains_books(
            [book_belarusian, book_both_languages])
        self._assert_page_does_not_contain_books([book_russian])

        self._choose_filter('#filter-language', 'усе')
        self._assert_page_contains_books(
            [book_russian, book_belarusian, book_both_languages])

        self._choose_filter('#filter-language', 'руская')
        self._assert_page_contains_books([book_russian, book_both_languages])
        self._assert_page_does_not_contain_books([book_belarusian])

        # Ensure that language filter remains when navigating to other pages.
        self.driver.find_element(By.LINK_TEXT,
                                 self.fake_data.tag_poetry.name).click()
        self._assert_page_contains_books([book_russian])
        self._assert_page_does_not_contain_books([book_belarusian])

    def test_price_filter(self):
        book_paid = self.fake_data.create_book_with_single_narration(
            title='Paid',
            tags=[self.fake_data.tag_poetry],
            paid=True,
        )
        book_free = self.fake_data.create_book_with_single_narration(
            title='Free',
            tags=[self.fake_data.tag_poetry],
            paid=False,
        )
        book_both = self.fake_data.create_book_with_single_narration(
            title='Both',
            paid=True,
        )
        models.Narration.objects.create(
            book=book_both,
            paid=False,
            duration=timedelta(minutes=15),
        )
        self.driver.get(f'{self.live_server_url}/catalog')

        self._choose_filter('#filter-price', 'платныя')
        self._assert_page_contains_books([book_paid, book_both])
        self._assert_page_does_not_contain_books([book_free])

        self._choose_filter('#filter-price', 'усе')
        self._assert_page_contains_books([book_paid, book_free, book_both])

        self._choose_filter('#filter-price', 'бясплатныя')
        self._assert_page_contains_books([book_free, book_both])
        self._assert_page_does_not_contain_books([book_paid])

        # Ensure that price filter remains when navigating to other pages.
        self.driver.find_element(By.LINK_TEXT,
                                 self.fake_data.tag_poetry.name).click()
        self._assert_page_contains_books([book_free])
        self._assert_page_does_not_contain_books([book_paid, book_both])
