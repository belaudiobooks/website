from tests.webdriver_test_case import WebdriverTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select


class LacinizationTests(WebdriverTestCase):
    '''Selenium tests for lacinization.'''

    def test_switch_language(self):
        book = self.fake_data.create_book_with_single_narration(
            title=f'Кніга пра каханне',
            authors=[self.fake_data.person_ales],
        )
        book.description = 'Апісанне кнігі'
        book.save()

        # Go to the main page and check that it is using cyrillic.
        self.driver.get(self.live_server_url)
        bel_title = 'Беларускія аўдыякнігі'
        self.assertEqual(bel_title, self.driver.title)
        self.assertEqual(
            bel_title.upper(),
            self.driver.find_element(By.CSS_SELECTOR, '.logo-title').text
        )
        self.assertEqual(
            'Кніга пра каханне',
            self.driver.find_element(By.CSS_SELECTOR, '[data-test="book-title"]').text
        )

        # Switch to lacink and check that it is using lacinka.
        Select(
            self.driver.find_element(By.CSS_SELECTOR, '#language-switcher')
        ).select_by_visible_text('łacinka')
        lac_title = 'Biełaruskija aŭdyjaknihi'
        self.assertEqual(lac_title, self.driver.title)
        self.assertEqual(
            lac_title.upper(),
            self.driver.find_element(By.CSS_SELECTOR, '.logo-title').text
        )
        book_link = self.driver.find_element(By.CSS_SELECTOR, '[data-test="book-title"]')
        self.assertEqual('Kniha pra kachańnie', book_link.text)

        # Go to the book page and check that it is still using lacinka.
        self.scroll_and_click(book_link)
        self.assertEqual(
            'Apisańnie knihi',
            self.driver.find_element(By.CSS_SELECTOR, '[data-test="book-description"]').text
        )
        self.assertEqual('Kniha Pra Kachańnie aŭdyjakniha', self.driver.title)

        # Switch to cyrillic and chec
        Select(
            self.driver.find_element(By.CSS_SELECTOR, '#language-switcher')
        ).select_by_visible_text('кірыліца')
        self.assertEqual(
            'Апісанне кнігі',
            self.driver.find_element(By.CSS_SELECTOR, '[data-test="book-description"]').text
        )
        self.assertEqual('Кніга Пра Каханне аўдыякніга', self.driver.title)
        self.assertEqual(
            bel_title.upper(),
            self.driver.find_element(By.CSS_SELECTOR, '.logo-title').text
        )

    def test_search_with_lacinka(self):
        book = self.fake_data.create_book_with_single_narration(
            title=f'Кніга пра каханне',
            authors=[self.fake_data.person_ales],
        )
        self.init_algolia()
        self.driver.get(self.live_server_url)
        Select(
            self.driver.find_element(By.CSS_SELECTOR, '#language-switcher')
        ).select_by_visible_text('łacinka')

        search = self.driver.find_element(By.CSS_SELECTOR, '#search')
        search.send_keys('kach')
        self.wait_for_search_suggestion('Kniha pra kachańnieA. Alesiavič',
                                        f'/books/{book.slug}')