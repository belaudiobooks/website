from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class PublisherPageTests(WebdriverTestCase):
    """Selenium tests for publisher page."""

    def setUp(self):
        super().setUp()
        self.publisher = self.fake_data.publisher_audiobooksby
        self.books = [
            self.fake_data.create_book_with_single_narration(
                title="Book 1",
                publishers=[self.publisher],
            ),
            self.fake_data.create_book_with_single_narration(
                title="Book 2",
                publishers=[self.publisher],
            ),
        ]

    def _get_publisher_url(self) -> str:
        return f"{self.live_server_url}/publisher/{self.publisher.slug}"

    def _check_book_present(self, book: models.Book) -> None:
        found = False
        for elem in self.driver.find_elements(By.LINK_TEXT, book.title):
            found = found or elem.get_dom_attribute("href") == f"/books/{book.slug}"
        self.assertTrue(found, f"Did not find link for book {book.title} {book.slug}")

    def test_books_published(self):
        self.driver.get(self._get_publisher_url())
        for book in self.books:
            self._check_book_present(book)

    def test_page_elements(self):
        self.driver.get(self._get_publisher_url())
        self.assertEqual(f"{self.publisher.name}, аўдыякнігі", self.driver.title)
        description = self.driver.find_element(
            By.CSS_SELECTOR, 'meta[name="description"]'
        ).get_dom_attribute("content")
        self.assertIn(self.publisher.name, description)
        publisher_name = self.driver.find_element(
            By.CSS_SELECTOR, "#publisher-details h1"
        ).text
        self.assertIn(self.publisher.name, publisher_name)
        publisher_url = self.driver.find_element(
            By.CSS_SELECTOR, "#publisher-details a"
        )
        self.assertIn(self.publisher.url, publisher_url.text)
        self.assertIn(self.publisher.url, publisher_url.get_dom_attribute("href"))
        publisher_description = self.driver.find_elements(
            By.CSS_SELECTOR, "#publisher-details p"
        )
        for paragraph in publisher_description:
            if not paragraph.text:
                continue
            self.assertIn(paragraph.text, self.publisher.description)
