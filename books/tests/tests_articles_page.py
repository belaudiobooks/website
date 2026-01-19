from books.views import articles
from books.tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By
from django.urls import reverse


class ArticlesPageTest(WebdriverTestCase):
    """Selenium tests for artciels page."""

    def test_articles_link_redirects_to_first_article(self):
        self.driver.get(self.live_server_url)
        self.driver.find_element(By.LINK_TEXT, "Артыкулы").click()
        first_article = articles.ARTICLES[0]
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "h1").text, first_article.title
        )

    def test_article_page(self):
        article = articles.ARTICLES[0]
        self.driver.get(
            self.live_server_url + reverse("single-article", args=(article.slug,))
        )
        self.assertEqual(
            self.driver.find_element(By.CSS_SELECTOR, "h1").text, article.title
        )
        self.assertEqual(
            self.driver.find_element(
                By.CSS_SELECTOR, "meta[name=description]"
            ).get_attribute("content"),
            article.short_description,
        )
