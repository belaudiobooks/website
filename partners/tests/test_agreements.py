from dataclasses import dataclass
from decimal import Decimal
from typing import List

from selenium.webdriver.common.by import By

from partners.models import Agreement, Partner
from partners.tests.webdriver_test_case import WebdriverTestCase


@dataclass
class RenderedItem:
    """Represents a row in the agreements table."""

    title: str
    authors: List[str]
    status: str
    royalty: str


class AgreementsTest(WebdriverTestCase):
    def parse_agreements_table(self) -> List[RenderedItem]:
        """Parse the agreements table from the page and return list of RenderedItem."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-test-id='agreement-row']"
        )
        items = []
        for row in rows:
            title = row.find_element(By.CSS_SELECTOR, "[data-test-id='title']").text
            authors_text = row.find_element(
                By.CSS_SELECTOR, "[data-test-id='authors']"
            ).text
            authors = authors_text.split("\n") if authors_text else []
            status = row.find_element(
                By.CSS_SELECTOR, "[data-test-id='status']"
            ).text.strip()
            royalty = row.find_element(By.CSS_SELECTOR, "[data-test-id='royalty']").text
            items.append(
                RenderedItem(
                    title=title, authors=authors, status=status, royalty=royalty
                )
            )
        return items

    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated users should be redirected to login page."""
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/"
        )
        self.assertIn("/partners/login/", self.driver.current_url)

    def test_user_from_different_partner_gets_forbidden(self):
        """User from a different partner should get 403."""
        other_partner = Partner.objects.create(name="Other Partner")
        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{other_partner.id}/agreements/"
        )
        # HttpResponseForbidden returns empty body, so check agreements page is not shown
        self.assertNotIn("Дамовы", self.driver.page_source)

    def test_authenticated_user_can_view_agreements_page(self):
        """Authenticated user can access their agreements page."""
        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/"
        )
        self.assertIn("Дамовы", self.driver.page_source)

    def test_empty_agreements_shows_message(self):
        """When there are no agreements, show appropriate message."""
        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/"
        )
        empty_message = self.driver.find_element(
            By.CSS_SELECTOR, "[data-test-id='empty-message']"
        )
        self.assertEqual("Дамоваў пакуль няма.", empty_message.text)

    def test_agreement_with_narration_displayed(self):
        """Agreement with a narration should display book title and royalty."""
        # Create a book with narration using FakeData
        fake = self.books_fake_data
        book = fake.create_book_with_single_narration(
            title="Тэставая кніга",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )
        narration = book.narrations.first()

        # Create agreement with this narration
        agreement = Agreement.objects.create(
            partner=self.partner, royalty_percent=Decimal("15.00")
        )
        agreement.narrations.add(narration)

        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/"
        )

        items = self.parse_agreements_table()
        self.assertEqual(
            items,
            [
                RenderedItem(
                    "Тэставая кніга", ["Алесь Алесявіч"], "Апублікавана", "15%"
                ),
            ],
        )

    def test_agreement_with_book_displayed(self):
        """Agreement with books should display titles and royalty."""
        fake = self.books_fake_data
        book1 = fake.create_book_with_single_narration(
            title="Будучая кніга",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )
        book2 = fake.create_book_with_single_narration(
            title="Яшчэ адна кніга",
            authors=[fake.person_viktar],
            narrators=[fake.person_volha],
        )

        agreement = Agreement.objects.create(
            partner=self.partner,
            royalty_percent=Decimal("10.50"),
        )
        agreement.books.add(book1, book2)

        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/"
        )

        items = self.parse_agreements_table()
        self.assertEqual(
            items,
            [
                RenderedItem(
                    "Будучая кніга", ["Алесь Алесявіч"], "Не апублікавана", "10.50%"
                ),
                RenderedItem(
                    "Яшчэ адна кніга",
                    ["Віктар Віктаравіч"],
                    "Не апублікавана",
                    "10.50%",
                ),
            ],
        )

    def test_multiple_agreements_displayed(self):
        """Multiple agreements should all be displayed."""
        fake = self.books_fake_data
        book1 = fake.create_book_with_single_narration(
            title="Кніга 1",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )
        book2 = fake.create_book_with_single_narration(
            title="Кніга 2",
            authors=[fake.person_viktar],
            narrators=[fake.person_volha],
        )

        # First agreement with a book
        agreement1 = Agreement.objects.create(
            partner=self.partner,
            royalty_percent=Decimal("20.00"),
        )
        agreement1.books.add(book1)

        # Second agreement with different royalty
        agreement2 = Agreement.objects.create(
            partner=self.partner,
            royalty_percent=Decimal("25.00"),
        )
        agreement2.books.add(book2)

        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/"
        )

        items = self.parse_agreements_table()
        self.assertEqual(
            items,
            [
                RenderedItem("Кніга 1", ["Алесь Алесявіч"], "Не апублікавана", "20%"),
                RenderedItem(
                    "Кніга 2", ["Віктар Віктаравіч"], "Не апублікавана", "25%"
                ),
            ],
        )
