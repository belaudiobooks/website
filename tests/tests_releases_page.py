from datetime import date
from books.models import BookStatus
from tests.webdriver_test_case import WebdriverTestCase


class ReleasesPageTests(WebdriverTestCase):
    """Selenium tests for releases page."""

    def test_title_correct(self):
        self.driver.get(f"{self.live_server_url}/releases/2021")
        self.assertEqual("Навінкі 2021 года", self.driver.title)

        self.driver.get(f"{self.live_server_url}/releases/2021/02")
        self.assertEqual("Навінкі лютага 2021", self.driver.title)

        self.driver.get(f"{self.live_server_url}/releases/2021/-1")
        self.assertEqual("Page not found at /releases/2021/-1", self.driver.title)

        self.driver.get(f"{self.live_server_url}/releases/2021/1000")
        self.assertEqual("Старонка не знойдзена", self.driver.title)

    def test_releases_for_year(self):
        match1 = self.fake_data.create_book_with_single_narration(
            title="Book 2023 one",
            authors=[self.fake_data.person_ales],
            date=date(2023, 1, 1),
        )
        match2 = self.fake_data.create_book_with_single_narration(
            title="Book 2023 two",
            authors=[self.fake_data.person_ales],
            date=date(2023, 2, 1),
        )
        miss1 = self.fake_data.create_book_with_single_narration(
            title="Book 2022",
            authors=[self.fake_data.person_ales],
            date=date(2022, 1, 1),
        )
        miss2 = self.fake_data.create_book_with_single_narration(
            title="Book 2024",
            authors=[self.fake_data.person_ales],
            date=date(2024, 1, 1),
        )

        self.driver.get(f"{self.live_server_url}/releases/2023")
        self.assert_page_contains_books([match1, match2])
        self.assert_page_does_not_contain_books([miss1, miss2])

    def test_releases_for_month(self):
        match1 = self.fake_data.create_book_with_single_narration(
            title="Book Feb 2023 one",
            authors=[self.fake_data.person_ales],
            date=date(2023, 2, 1),
        )
        match2 = self.fake_data.create_book_with_single_narration(
            title="Book Feb 2023 two",
            authors=[self.fake_data.person_ales],
            date=date(2023, 2, 10),
        )
        miss1 = self.fake_data.create_book_with_single_narration(
            title="Book Jan 2023",
            authors=[self.fake_data.person_ales],
            date=date(2023, 1, 1),
        )
        miss2 = self.fake_data.create_book_with_single_narration(
            title="Book Mar 2023",
            authors=[self.fake_data.person_ales],
            date=date(2023, 3, 1),
        )
        miss3 = self.fake_data.create_book_with_single_narration(
            title="Book Feb 2022",
            authors=[self.fake_data.person_ales],
            date=date(2022, 2, 1),
        )

        self.driver.get(f"{self.live_server_url}/releases/2023/02")
        self.assert_page_contains_books([match1, match2])
        self.assert_page_does_not_contain_books([miss1, miss2, miss3])

    def test_inactive_books_are_hidden(self):
        match = self.fake_data.create_book_with_single_narration(
            title="Book 2023 one",
            authors=[self.fake_data.person_ales],
            date=date(2023, 1, 1),
        )
        miss = self.fake_data.create_book_with_single_narration(
            title="Book 2023 two",
            authors=[self.fake_data.person_ales],
            date=date(2023, 1, 1),
        )
        miss.status = BookStatus.HIDDEN
        miss.save()
        self.driver.get(f"{self.live_server_url}/releases/2023")
        self.assert_page_contains_books([match])
        self.assert_page_does_not_contain_books([miss])
