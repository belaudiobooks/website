from tests.webdriver_test_case import WebdriverTestCase


class StatsPagesTest(WebdriverTestCase):
    """Tests for various robot-related pages like robots.txt, sitemap."""

    def test_digest_page(self):
        self.fake_data.create_book_with_single_narration(title="Book")
        self.fake_data.create_book_with_single_narration(title="Book 2")

        # Just verify that it renders without errors.
        # TODO: Add more checks.
        self.driver.get(f"{self.live_server_url}/stats/digest")

    def test_birthdays_page(self):
        # Just verify that it renders without errors.
        # TODO: Add more checks.
        self.fake_data.create_book_with_single_narration(title="Book")
        self.fake_data.create_book_with_single_narration(title="Book 2")
        self.driver.get(f"{self.live_server_url}/stats/birthdays")
