from books.tests.webdriver_test_case import WebdriverTestCase


class AboutUsPageTests(WebdriverTestCase):
    """Selenium tests for about us page."""

    def test_page_elements(self):
        self.driver.get(f"{self.live_server_url}/about")
        self.assertEqual("Пра нас", self.driver.title)
