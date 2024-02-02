from datetime import date, timedelta
from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By


class HeaderAndSearchTests(WebdriverTestCase):
    """Selenium tests for header elements including search."""

    def setUp(self):
        super().setUp()
        self.book = models.Book.objects.create(
            title="Кніга пра каханне",
            title_ru="Книга о любви",
            slug="kniga-pra-kakhanne",
            status=models.BookStatus.ACTIVE,
        )
        self.book.authors.set([self.fake_data.person_ales])
        narration = models.Narration.objects.create(
            book=self.book,
            language=models.Language.BELARUSIAN,
            duration=timedelta(hours=14, minutes=15),
            date=date.today(),
        )
        narration.publishers.set([self.fake_data.publisher_audiobooksby])

    def test_click_logo_leads_to_main_page(self):
        self.driver.get(f"{self.live_server_url}/catalog")
        self.driver.find_element(By.CSS_SELECTOR, "nav .logo").click()
        self.assertEqual(f"{self.live_server_url}/", self.driver.current_url)

    def test_click_site_title_to_main_page(self):
        self.driver.get(f"{self.live_server_url}/catalog")
        self.driver.find_element(By.CSS_SELECTOR, "nav .site-title").click()
        self.assertEqual(f"{self.live_server_url}/", self.driver.current_url)

    def test_click_catalog(self):
        self.driver.get(self.live_server_url)
        self.driver.find_element(By.CSS_SELECTOR, "nav .catalog").click()
        self.assertEqual(f"{self.live_server_url}/catalog", self.driver.current_url)

    def test_click_about_us(self):
        self.driver.get(self.live_server_url)
        self.driver.find_element(By.CSS_SELECTOR, "nav .about-us").click()
        self.assertEqual(f"{self.live_server_url}/about", self.driver.current_url)

    def test_client_side_search_book(self):
        self.init_algolia_or_skip_test()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, "#search")
        for query in ["каханне", "КАХАННЕ", "ЛюБвИ"]:
            search.clear()
            search.send_keys(query)
            self.wait_for_search_suggestion(
                "Кніга пра каханнеА. Алесявіч", "/books/kniga-pra-kakhanne"
            )

    def test_client_side_search_author(self):
        self.init_algolia_or_skip_test()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, "#search")
        for query in ["алесь", "АЛЕСЬ", "Александр"]:
            search.clear()
            search.send_keys(query)
            self.wait_for_search_suggestion("Алесь Алесявіч", "/person/ales-alesievich")

    def test_client_side_search_publisher(self):
        self.init_algolia_or_skip_test()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, "#search")
        for query in ["audiob", "audiobooks.by", "AUDIOBO"]:
            search.clear()
            search.send_keys(query)
            self.wait_for_search_suggestion(
                "audiobooks.by",
                f"/publisher/{self.fake_data.publisher_audiobooksby.slug}",
            )

    def test_server_side_searc_author(self):
        self.init_algolia_or_skip_test()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, "#search")
        search.send_keys("алесявіч")
        self.driver.find_element(By.CSS_SELECTOR, "#button-search").click()
        self.assertIn("/search", self.driver.current_url)
        search_results = self.driver.find_elements(By.CSS_SELECTOR, "#books .card")
        self.assertEqual(
            "Вынікі пошука 'алесявіч'",
            self.driver.find_element(By.CSS_SELECTOR, "#searched-query").text,
        )

        # Search should return author himself plus all his books (one book).
        self.assertEqual(2, len(search_results))

        # First item should be author.
        item = search_results[0]
        self.assertEqual(self.fake_data.person_ales.name, item.text.strip())
        self.assertEqual(
            "/person/ales-alesievich",
            item.find_element(by=By.CSS_SELECTOR, value="a").get_dom_attribute("href"),
        )

        item = self.driver.find_element(
            By.CSS_SELECTOR, f'a[href="/books/{self.book.slug}"] .card-title'
        )
        self.assertIsNotNone(item)
        self.assertIn(self.book.title, item.text)

    def test_server_side_search_publisher(self):
        self.init_algolia_or_skip_test()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, "#search")
        search.send_keys("audiobooks.by")
        self.driver.find_element(By.CSS_SELECTOR, "#button-search").click()
        self.assertIn("/search", self.driver.current_url)
        search_results = self.driver.find_elements(By.CSS_SELECTOR, "#books .card")
        self.assertEqual(
            "Вынікі пошука 'audiobooks.by'",
            self.driver.find_element(By.CSS_SELECTOR, "#searched-query").text,
        )

        # Search should return author himself plus all his books (one book).
        self.assertEqual(2, len(search_results))

        # First item should be publisher.
        item = search_results[0]
        self.assertEqual(self.fake_data.publisher_audiobooksby.name, item.text.strip())
        self.assertEqual(
            "/publisher/audiobooksby",
            item.find_element(by=By.CSS_SELECTOR, value="a").get_dom_attribute("href"),
        )
        # Second item should be a book of this publisher
        item = self.driver.find_element(
            By.CSS_SELECTOR, f'a[href="/books/{self.book.slug}"] .card-title'
        )
        self.assertIsNotNone(item)
        self.assertIn(self.book.title, item.text)
