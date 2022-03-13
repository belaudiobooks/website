from books import models
from tests.webdriver_test_case import WebdriverTestCase


class CatalogPageTests(WebdriverTestCase):
    '''Selenium tests for catalog page.'''

    def test_genre_page(self):
        tag = models.Tag.objects.filter(name='Сучасная проза').first()
        self.driver.get(f'{self.live_server_url}/books?books={tag.slug}')
        self.assertEqual(tag.name, self.driver.title)