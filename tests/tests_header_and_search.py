from datetime import date, timedelta
import time
from books import models
from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By


class HeaderAndSearchTests(WebdriverTestCase):
    '''Selenium tests for header elements including search.'''

    # TODO: #90 - remove once all tests switch to using fake data.
    fixtures = []

    def setUp(self):
        super().setUp()
        self.book = models.Book.objects.create(
            title='Кніга пра каханне',
            title_ru='Книга о любви',
            slug='kniga-pra-kakhanne',
            date=date.today(),
            status=models.BookStatus.ACTIVE,
        )
        self.book.authors.set([self.fake_data.person_ales])
        narration = models.Narration.objects.create(
            book=self.book,
            language=models.Language.BELARUSIAN,
            duration=timedelta(hours=14, minutes=15),
        )
        narration.publishers.set([self.fake_data.publisher_audiobooksby])

    def test_click_logo_leads_to_main_page(self):
        self.driver.get(f'{self.live_server_url}/catalog')
        self.driver.find_element(By.CSS_SELECTOR, 'nav .logo').click()
        self.assertEqual(f'{self.live_server_url}/', self.driver.current_url)

    def test_click_site_title_to_main_page(self):
        self.driver.get(f'{self.live_server_url}/catalog')
        self.driver.find_element(By.CSS_SELECTOR, 'nav .site-title').click()
        self.assertEqual(f'{self.live_server_url}/', self.driver.current_url)

    def test_click_catalog(self):
        self.driver.get(self.live_server_url)
        self.driver.find_element(By.CSS_SELECTOR, 'nav .catalog').click()
        self.assertEqual(f'{self.live_server_url}/catalog',
                         self.driver.current_url)

    def test_click_about_us(self):
        self.driver.get(self.live_server_url)
        self.driver.find_element(By.CSS_SELECTOR, 'nav .about-us').click()
        self.assertEqual(f'{self.live_server_url}/about',
                         self.driver.current_url)

    def _wait_for_suggestion(self, text: str, link: str) -> None:
        autocomplete = self.driver.find_element(By.CSS_SELECTOR,
                                                '#autocomplete')
        time.sleep(1)
        element = WebDriverWait(self.driver, 10).until(
            lambda wd: autocomplete.find_element(by=By.LINK_TEXT, value=text),
            f'Did not see suggestion with text "{text}"')
        self.assertEqual(link, element.get_dom_attribute('href'))

    def _init_algolia(self) -> None:
        self.driver.get(f'{self.live_server_url}/push_data_to_algolia')

    def test_client_side_search_book(self):
        self._init_algolia()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, '#search')
        for query in ['каханне', 'КАХАННЕ', 'ЛюБвИ']:
            search.clear()
            search.send_keys(query)
            self._wait_for_suggestion(f'Кніга пра каханнеА. Алесявіч',
                                      '/books/kniga-pra-kakhanne')

    def test_client_side_search_author(self):
        self._init_algolia()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, '#search')
        for query in ['алесь', 'АЛЕСЬ', 'Александр']:
            search.clear()
            search.send_keys(query)
            self._wait_for_suggestion('Алесь Алесявіч',
                                      '/person/ales-alesievich')

    def test_client_side_search_publisher(self):
        self._init_algolia()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, '#search')
        for query in ['audiob', 'audiobooks.by', 'AUDIOBO']:
            search.clear()
            search.send_keys(query)
            self._wait_for_suggestion(
                'audiobooks.by',
                f'/publisher/{self.fake_data.publisher_audiobooksby.slug}')

    def test_server_side_search(self):
        self._init_algolia()
        self.driver.get(self.live_server_url)
        search = self.driver.find_element(By.CSS_SELECTOR, '#search')
        search.send_keys('алесявіч')
        self.driver.find_element(By.CSS_SELECTOR, '#button-search').click()
        self.assertIn('/search', self.driver.current_url)
        search_results = self.driver.find_elements(By.CSS_SELECTOR,
                                                   '#books .card')
        self.assertEqual(
            f'Вынікі пошука \'алесявіч\'',
            self.driver.find_element(By.CSS_SELECTOR, '#searched-query').text)

        # Search should return author himself plus all his books (one book).
        self.assertEqual(2, len(search_results))

        # First item should be author.
        item = search_results[0]
        self.assertEqual(self.fake_data.person_ales.name, item.text.strip())
        self.assertEqual(
            f'/person/ales-alesievich',
            item.find_element(by=By.CSS_SELECTOR,
                              value='a').get_dom_attribute('href'))

        item = self.driver.find_element(
            By.CSS_SELECTOR, f'a[href="/books/{self.book.slug}"] .card-title')
        self.assertIsNotNone(item)
        self.assertIn(self.book.title, item.text)
