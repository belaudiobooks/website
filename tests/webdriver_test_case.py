import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from books import models
from tests import fake_data


# Uncomment to run tests in debug mode. Useful when server returns 500 and test fails
# without any useful info in logs.
@override_settings(DEBUG=True)
class WebdriverTestCase(StaticLiveServerTestCase):
    '''Base class for all webdriver tests. Initializes webdriver and seeds DB.'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        cls.driver = webdriver.Chrome(options=options,
                                      service=ChromeService(
                                          ChromeDriverManager().install()))
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.fake_data = fake_data.FakeData()

    def tearDown(self):
        super().tearDown()
        self.fake_data.cleanup()

    def scroll_into_view(self, element: WebElement) -> WebElement:
        '''
        Scrolls given element into view. Needed for elements
        below the fold to make them clickable.
        '''
        self.driver.execute_script(
            'arguments[0].scrollIntoView({block: "center"})', element)
        # Need to add sleep as scrolling doesn't finish quickly as expected_conditions
        # don't work for some reason.
        time.sleep(1)
        return element

    def scroll_and_click(self, element: WebElement) -> None:
        '''Scroll and clicks.'''
        self.scroll_into_view(element).click()

    def assert_page_contains_only_books_of_link_type(
            self, link_type: models.LinkType) -> None:
        '''
        Verifies that current page contains non-empty list of books and all
        books have at least one link of the given type. This is used for tests
        that verify filtering by link type.
        '''
        books_links = self.driver.find_elements(By.CSS_SELECTOR,
                                                'a[data-type="book-title"]')
        self.assertNotEqual(books_links, [])
        for book_link in books_links:
            slug = book_link.get_attribute('href').split('/')[-1]
            book = models.Book.objects.get(slug=slug)
            narrations = list(
                book.narrations.filter(links__url_type__name=link_type.name))
            self.assertNotEqual(
                narrations, [],
                f'Book {book.title} does not have links of type {link_type.name}'
            )
