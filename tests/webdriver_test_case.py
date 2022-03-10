import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement


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

    def scroll_into_view(self, element: WebElement) -> None:
        '''
        Scrolls given element into view. Needed for elements 
        below the fold to make them clickable.
        '''
        self.driver.execute_script(
            'arguments[0].scrollIntoView({block: "center"})', element)
        # Need to add sleep as scrolling doesn't finish quickly as expected_conditions
        # don't work for some reason.
        time.sleep(1)
