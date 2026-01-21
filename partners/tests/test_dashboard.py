from partners.tests.webdriver_test_case import WebdriverTestCase


class DashboardTest(WebdriverTestCase):
    def test_index_page_has_hello_world(self):
        self.driver.get(f"{self.live_server_url}/partners/")
        self.assertIn("Hello World", self.driver.page_source)
