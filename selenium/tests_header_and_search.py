from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from selenium import webdriver
from books import models


class HeaderAndSearchTests(StaticLiveServerTestCase):
    '''Selenium tests for header elements including search.'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)

    def setUp(self):
        call_command('loaddata', 'data/data.json')

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

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
