import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from books import models


class WebdriverTestCase(StaticLiveServerTestCase):
    '''Base class for all webdriver tests. Initializes webdriver and seeds DB.'''

    fixtures = ['data/data.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

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
