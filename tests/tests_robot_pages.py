import requests
from books import models
from tests.webdriver_test_case import WebdriverTestCase


class RobotPagesTests(WebdriverTestCase):
    '''Tests for various robot-related pages like robots.txt, sitemap.'''

    def test_sitemap_contains_book_person_tag(self) -> None:
        domain = self.live_server_url
        robots = requests.get(f'{domain}/robots.txt').text
        sitemap_url = None
        for line in robots.splitlines():
            if line.startswith('Sitemap:'):
                sitemap_url = line.removeprefix('Sitemap:').strip()
        self.assertIsNotNone(sitemap_url)

        sitemap = requests.get(sitemap_url).text.splitlines()
        self.assertIn(f'{domain}/', sitemap)
        self.assertIn(f'{domain}/catalog', sitemap)
        self.assertIn(f'{domain}/about', sitemap)

        person = models.Person.objects.filter(name='Андрэй Хадановіч').first()
        self.assertIn(f'{domain}/person/{person.slug}', sitemap)

        book = models.Book.objects.filter(title='Людзі на балоце').first()
        self.assertIn(f'{domain}/books/{book.slug}', sitemap)

        tag = models.Tag.objects.filter(name='Сучасная проза').first()
        self.assertIn(f'{domain}/catalog/{tag.slug}', sitemap)
