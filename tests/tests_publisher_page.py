from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class PublisherPageTests(WebdriverTestCase):
    """Selenium tests for publisher page."""

    def setUp(self):
        super().setUp()
        self.publisher = models.Publisher.objects.filter(
            name="audiobooks.by").first()

    def _get_publisher_url(self) -> str:
        return f"{self.live_server_url}/publisher/{self.publisher.slug}"

    def _check_book_present(self, book: models.Book) -> None:
        found = False
        for elem in self.driver.find_elements(By.LINK_TEXT, book.title):
            found = found or elem.get_dom_attribute(
                "href") == f"/books/{book.slug}"
        self.assertTrue(
            found, f"Did not find link for book {book.title} {book.slug}")

    def test_books_published(self):
        self.driver.get(self._get_publisher_url())
        self.assertGreaterEqual(self.publisher.narrations.count(), 1)
        for narration in self.publisher.narrations.all():
            self._check_book_present(narration.book)

    def test_page_elements(self):
        self.driver.get(self._get_publisher_url())
        self.assertEqual(f'{self.publisher.name}, аўдыякнігі', self.driver.title)
        description = self.driver.find_element(
            By.CSS_SELECTOR,
            'meta[name="description"]').get_dom_attribute('content')
        self.assertIn(self.publisher.name, description)
        publisher_description = self.driver.find_element(
            By.CSS_SELECTOR,
            '.col-12.col-md-3.mt-2.mt-sm-5').text
        self.assertIn(self.publisher.name, publisher_description)
        self.assertIn(self.publisher.url, publisher_description)