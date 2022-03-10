from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from selenium import webdriver
from books import models


class HomePageTests(StaticLiveServerTestCase):
    '''Selenium tests for home-page related stuff.'''

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

    def test_click_book_title(self):
        self.driver.get(self.live_server_url)
        book = self.get_first_book()
        self.driver.find_element_by_link_text(book.title).click()
        self.assertIn(f'/books/{book.slug}', self.driver.current_url)

    def test_click_book_cover(self):
        self.driver.get(self.live_server_url)
        book = self.get_first_book()
        self.driver.find_element_by_css_selector(
            f'img[alt="{book.title}"]').click()
        self.assertIn(f'/books/{book.slug}', self.driver.current_url)

    def test_click_book_author(self):
        self.driver.get(self.live_server_url)
        book = self.get_first_book()
        author = book.authors.first()
        self.driver.find_element_by_link_text(author.name).click()
        self.assertIn(f'/person/{author.slug}', self.driver.current_url)

    def test_page_elements(self):
        self.driver.get(self.live_server_url)
        self.assertEqual('Беларускія аўдыякнігі', self.driver.title)