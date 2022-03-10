from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from selenium import webdriver
from books import models


class AboutUsPageTests(StaticLiveServerTestCase):
    '''Selenium tests for about us page.'''

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

    def test_page_elements(self):
        self.driver.get(f'{self.live_server_url}/about')
        self.assertEqual('Пра нас', self.driver.title)