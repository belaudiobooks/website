from datetime import date, timedelta
from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class HomePageTests(WebdriverTestCase):
    """Selenium tests for home-page related stuff."""

    def setUp(self):
        super().setUp()
        self.books = []
        for i in range(6):
            book = self.fake_data.create_book_with_single_narration(
                title=f"Book {i + 1}",
                authors=[self.fake_data.person_ales],
            )
            narration = book.narrations.first()
            narration.cover_image = self.fake_data.create_image()
            narration.save()
            self.books.append(book)

    def get_first_book(self) -> models.Book:
        return models.Book.objects.active_books_ordered_by_date().first()

    def test_click_book_title(self):
        self.driver.get(self.live_server_url)
        book = self.books[0]
        title = self.driver.find_element(By.LINK_TEXT, book.title)
        self.scroll_and_click(title)
        self.assertIn(f"/books/{book.slug}", self.driver.current_url)

    def test_click_book_cover(self):
        self.driver.get(self.live_server_url)
        book = self.books[0]
        cover_selector = f'img[alt="{book.title}"]'
        if book.narrations.first().cover_image == "":
            # when image is missing - find first auto-generated cover.
            # It should match the first book.
            cover_selector = ".cover-small"
        self.scroll_and_click(self.driver.find_element(By.CSS_SELECTOR, cover_selector))
        self.assertIn(f"/books/{book.slug}", self.driver.current_url)

    def test_click_book_author(self):
        self.driver.get(self.live_server_url)
        book = self.books[0]
        author = book.authors.first()
        author_elem = self.driver.find_element(By.LINK_TEXT, author.name)
        self.scroll_and_click(author_elem)
        self.assertIn(f"/person/{author.slug}", self.driver.current_url)

    def test_page_elements(self):
        self.driver.get(self.live_server_url)
        self.assertEqual("Беларускія аўдыякнігі", self.driver.title)

    def assert_genre_section_correct(
        self, tag: models.Tag, expected_more_books_text: str
    ):
        section = self.driver.find_element(
            By.CSS_SELECTOR, f'[data-test="tag-{tag.slug}"]'
        )
        self.assertEqual(self.count_elements(".card", section), 6)
        more_books = section.find_element(By.CSS_SELECTOR, ".tag-selected")
        self.assertEqual(more_books.text, expected_more_books_text)
        self.assertIn(f"/catalog/{tag.slug}", more_books.get_attribute("href"))

    def test_book_count_for_genre_is_correct(self):
        for i in range(10):
            book = self.fake_data.create_book_with_single_narration(
                title=f"Book Contemp {i + 1}",
                authors=[self.fake_data.person_ales],
                tags=[self.fake_data.tag_contemporary],
            )
            book.save()
        for i in range(21):
            book = self.fake_data.create_book_with_single_narration(
                title=f"Book Classic {i + 1}",
                authors=[self.fake_data.person_ales],
                tags=[self.fake_data.tag_classics],
            )
            book.save()

        self.driver.get(self.live_server_url)

        self.assert_genre_section_correct(self.fake_data.tag_contemporary, "10 кніг")
        self.assert_genre_section_correct(self.fake_data.tag_classics, "21 кніга")

    def test_order_is_correct(self):
        b1, b2, b3, b4, b5, b6 = self.books

        def set_date(narration: models.Narration, day: int):
            narration.date = date.fromisoformat(f"2020-01-{day}")
            narration.save()

        # b1 = [Jan 15]
        set_date(b1.narrations.first(), 15)

        # b2 = [Jan 13, Jan 16]
        set_date(b2.narrations.first(), 13)
        b2_nar2 = models.Narration.objects.create(
            book=b2,
            language=models.Language.BELARUSIAN,
            date=date.today(),
        )
        set_date(b2_nar2, 16)

        # b3 = [Jan 17, Jan 12]
        set_date(b3.narrations.first(), 17)
        b3_nar2 = models.Narration.objects.create(
            book=b3,
            language=models.Language.BELARUSIAN,
            date=date.today(),
        )
        set_date(b3_nar2, 12)

        # b4 = [Jan 11]
        set_date(b4.narrations.first(), 11)

        # b5 = [Jan 18]
        set_date(b5.narrations.first(), 18)

        # b6 = [Jan 10]
        set_date(b6.narrations.first(), 10)

        self.driver.get(self.live_server_url)

        title_elements = self.driver.find_elements(
            By.CSS_SELECTOR, '[data-test="latest-books"] [data-test="book-title"]'
        )
        titles = [elem.text for elem in title_elements]
        self.assertEqual(
            titles,
            [
                b5.title,
                b3.title,
                b2.title,
                b1.title,
                b4.title,
                b6.title,
            ],
        )

    def test_book_with_emoji_in_name(self):
        book = self.fake_data.create_book_with_single_narration(
            title="Book 😊",
            authors=[self.fake_data.person_ales],
            date=date.today() + timedelta(days=1),
        )
        narration = book.narrations.first()
        narration.cover_image = self.fake_data.create_image()
        narration.save()

        self.assertEqual(book.title, "Book 😊")
        self.assertEqual(book.slug, "book")

        self.driver.get(self.live_server_url)
        title = self.driver.find_element(By.LINK_TEXT, book.title)
        self.scroll_and_click(title)
        self.assertIn(f"/books/{book.slug}", self.driver.current_url)
