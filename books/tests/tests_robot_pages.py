import requests
from books.views import articles
from books.tests.webdriver_test_case import WebdriverTestCase


class RobotPagesTests(WebdriverTestCase):
    """Tests for various robot-related pages like robots.txt, sitemap."""

    def setUp(self):
        super().setUp()
        self.book = self.fake_data.create_book_with_single_narration(title="Book")

    def get_sitemap_url(self) -> str:
        robots = requests.get(f"{self.live_server_url}/robots.txt").text
        sitemap_url = None
        for line in robots.splitlines():
            if line.startswith("Sitemap:"):
                sitemap_url = line.removeprefix("Sitemap:").strip()
        self.assertIsNotNone(sitemap_url)
        return sitemap_url

    def test_sitemap_contains_book_person_tag(self):
        article = articles.ARTICLES[0]
        domain = self.live_server_url
        sitemap = requests.get(self.get_sitemap_url()).text.splitlines()
        self.assertIn(f"{domain}/", sitemap)
        self.assertIn(f"{domain}/catalog", sitemap)
        self.assertIn(f"{domain}/about", sitemap)
        self.assertIn(f"{domain}/articles", sitemap)

        self.assertIn(f"{domain}/person/{self.fake_data.person_ales.slug}", sitemap)
        self.assertIn(f"{domain}/books/{self.book.slug}", sitemap)
        self.assertIn(f"{domain}/catalog/{self.fake_data.tag_classics.slug}", sitemap)
        self.assertIn(f"{domain}/articles/{article.slug}", sitemap)
        self.assertIn(
            f"{domain}/publisher/{self.fake_data.publisher_audiobooksby.slug}", sitemap
        )

    def test_all_sitemap_links_return_200(self):
        sitemap = requests.get(self.get_sitemap_url()).text.splitlines()

        for url in sitemap:
            self.assertIn(
                requests.head(url, timeout=20).status_code,
                [200, 302],
                f"Bad return code for url {url}",
            )
