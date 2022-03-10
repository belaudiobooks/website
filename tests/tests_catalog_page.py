from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from selenium import webdriver
from books import models


class CatalogPageTests(StaticLiveServerTestCase):
    '''Selenium tests for catalog page.'''

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

    def test_genre_page(self):
        tag = models.Tag.objects.filter(name='Сучасная проза').first()
        self.driver.get(f'{self.live_server_url}/books?books={tag.slug}')
        self.assertEqual(tag.name, self.driver.title)