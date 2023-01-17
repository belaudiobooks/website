import requests
from books import models, views
from tests.webdriver_test_case import WebdriverTestCase
from tests.worker import fetch_head_urls


class RobotPagesTests(WebdriverTestCase):
    '''Tests for various robot-related pages like robots.txt, sitemap.'''

    def get_sitemap_url(self) -> str:
        robots = requests.get(f'{self.live_server_url}/robots.txt').text
        sitemap_url = None
        for line in robots.splitlines():
            if line.startswith('Sitemap:'):
                sitemap_url = line.removeprefix('Sitemap:').strip()
        self.assertIsNotNone(sitemap_url)
        return sitemap_url

    def test_sitemap_contains_book_person_tag(self) -> None:
        domain = self.live_server_url
        sitemap = requests.get(self.get_sitemap_url()).text.splitlines()
        self.assertIn(f'{domain}/', sitemap)
        self.assertIn(f'{domain}/catalog', sitemap)
        self.assertIn(f'{domain}/about', sitemap)
        self.assertIn(f'{domain}/articles', sitemap)

        person = models.Person.objects.filter(name='Андрэй Хадановіч').first()
        self.assertIn(f'{domain}/person/{person.slug}', sitemap)

        book = models.Book.objects.filter(title='Людзі на балоце').first()
        self.assertIn(f'{domain}/books/{book.slug}', sitemap)

        tag = models.Tag.objects.filter(name='Сучасная проза').first()
        self.assertIn(f'{domain}/catalog/{tag.slug}', sitemap)

        article = views.ARTICLES[0]
        self.assertIn(f'{domain}/articles/{article.slug}', sitemap)

    def test_all_sitemap_links_return_200(self):
        sitemap = requests.get(self.get_sitemap_url()).text.splitlines()
        errors = [
            status for status in fetch_head_urls(sitemap)
            if status.response.status_code != 200
            and status.response.status_code != 302
        ]
        self.assertListEqual(errors, [])
