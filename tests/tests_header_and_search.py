from books import models
from tests.webdriver_test_case import WebdriverTestCase


class HeaderAndSearchTests(WebdriverTestCase):
    '''Selenium tests for header elements including search.'''

    def get_first_book(self) -> models.Book:
        return models.Book.objects.filter(title='Ордэн белай мышы').first()

    def test_click_logo_leads_to_main_page(self):
        self.driver.get(f'{self.live_server_url}/books')
        self.driver.find_element_by_css_selector('.navbar .logo').click()
        self.assertEqual(f'{self.live_server_url}/', self.driver.current_url)

    def test_click_site_title_to_main_page(self):
        self.driver.get(f'{self.live_server_url}/books')
        self.driver.find_element_by_css_selector('.navbar .site-title').click()
        self.assertEqual(f'{self.live_server_url}/', self.driver.current_url)

    def test_click_catalog(self):
        self.driver.get(self.live_server_url)
        self.driver.find_element_by_css_selector('.navbar .catalog').click()
        self.assertEqual(f'{self.live_server_url}/books',
                         self.driver.current_url)

    def test_click_about_u(self):
        self.driver.get(self.live_server_url)
        self.driver.find_element_by_css_selector('.navbar .about-us').click()
        self.assertEqual(f'{self.live_server_url}/about',
                         self.driver.current_url)
