import os
from dataclasses import dataclass
from decimal import Decimal
from typing import List

from django.core.files.uploadedfile import SimpleUploadedFile
from selenium.webdriver.common.by import By

from partners.models import Agreement, AgreementFile, Partner
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
                RenderedItem("Тэставая кніга", ["Алесь Алесявіч"], "Выдадзена", "15%"),
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
                    "Будучая кніга", ["Алесь Алесявіч"], "Не выдадзена", "10.50%"
                ),
                RenderedItem(
                    "Яшчэ адна кніга",
                    ["Віктар Віктаравіч"],
                    "Не выдадзена",
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
                RenderedItem("Кніга 1", ["Алесь Алесявіч"], "Не выдадзена", "20%"),
                RenderedItem("Кніга 2", ["Віктар Віктаравіч"], "Не выдадзена", "25%"),
            ],
        )

    def test_agreement_file_link_display(self):
        """Agreement file link shown only when file is attached."""
        fake = self.books_fake_data
        book_with_file = fake.create_book_with_single_narration(
            title="Кніга з дамовай",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )
        book_without_file = fake.create_book_with_single_narration(
            title="Кніга без дамовы",
            authors=[fake.person_viktar],
            narrators=[fake.person_volha],
        )

        # Create agreement with file
        agreement_with_file = Agreement.objects.create(
            partner=self.partner,
            royalty_percent=Decimal("15.00"),
        )
        agreement_with_file.books.add(book_with_file)
        pdf_file = SimpleUploadedFile(
            "agreement.pdf",
            b"%PDF-1.4 fake pdf content",
            content_type="application/pdf",
        )
        AgreementFile.objects.create(agreement=agreement_with_file, file=pdf_file)

        # Create agreement without file
        agreement_without_file = Agreement.objects.create(
            partner=self.partner,
            royalty_percent=Decimal("20.00"),
        )
        agreement_without_file.books.add(book_without_file)

        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/"
        )

        # Find all agreement file cells
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "[data-test-id='agreement-row']"
        )
        self.assertEqual(len(rows), 2)

        # First row (with file) should have a link
        file_cell_with = rows[0].find_element(
            By.CSS_SELECTOR, "[data-test-id='agreement-file']"
        )
        links_with = file_cell_with.find_elements(By.TAG_NAME, "a")
        self.assertEqual(len(links_with), 1)
        self.assertIn(
            f"/partners/{self.partner.id}/agreements/files/",
            links_with[0].get_attribute("href"),
        )

        # Second row (without file) should have no link
        file_cell_without = rows[1].find_element(
            By.CSS_SELECTOR, "[data-test-id='agreement-file']"
        )
        links_without = file_cell_without.find_elements(By.TAG_NAME, "a")
        self.assertEqual(len(links_without), 0)

    def test_agreement_file_download_works(self):
        """User can download agreement file when they have access."""
        fake = self.books_fake_data
        book = fake.create_book_with_single_narration(
            title="Кніга",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )

        pdf_content = b"%PDF-1.4 test pdf content for download"
        pdf_file = SimpleUploadedFile(
            "test_agreement.pdf", pdf_content, content_type="application/pdf"
        )

        agreement = Agreement.objects.create(
            partner=self.partner,
            royalty_percent=Decimal("10.00"),
        )
        agreement.books.add(book)
        agreement_file = AgreementFile.objects.create(
            agreement=agreement, file=pdf_file
        )

        # File should be downloaded to the current directory.
        # Verify that it does not exist before download.
        expected_file_name = agreement_file.file.name.split("/")[-1]
        self.assertFalse(os.path.exists(expected_file_name))

        self.login()

        # Navigate to the file URL
        self.driver.get(
            f"{self.live_server_url}/partners/{self.partner.id}/agreements/files/{agreement_file.id}/"
        )

        # For file downloads, Selenium will show the content or trigger download
        # We can verify that we didn't get redirected to login or get a 403/404 error page
        self.assertNotIn("/partners/login/", self.driver.current_url)
        self.assertNotIn("Forbidden", self.driver.page_source)
        self.assertNotIn("Not Found", self.driver.page_source)

        # Check that file exists and has expected content and clean it up.
        self.assertTrue(os.path.exists(expected_file_name))
        with open(expected_file_name, "rb") as f:
            content = f.read()
            self.assertEqual(content, pdf_content)
        os.remove(expected_file_name)

    def test_agreement_file_forbidden_for_other_partner(self):
        """User cannot download agreement file from another partner."""
        other_partner = Partner.objects.create(name="Other Partner")
        fake = self.books_fake_data
        book = fake.create_book_with_single_narration(
            title="Чужая кніга",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )

        pdf_content = b"%PDF-1.4 other partner pdf"
        pdf_file = SimpleUploadedFile(
            "other_agreement.pdf", pdf_content, content_type="application/pdf"
        )

        agreement = Agreement.objects.create(
            partner=other_partner,
            royalty_percent=Decimal("20.00"),
        )
        agreement.books.add(book)
        agreement_file = AgreementFile.objects.create(
            agreement=agreement, file=pdf_file
        )

        # File should be downloaded to the current directory.
        # Verify that it does not exist before download.
        expected_file_name = agreement_file.file.name.split("/")[-1]
        self.assertFalse(os.path.exists(expected_file_name))

        self.login()
        self.driver.get(
            f"{self.live_server_url}/partners/{other_partner.id}/agreements/files/{agreement_file.id}/"
        )

        # Make sure that file still does not exist.
        self.assertFalse(os.path.exists(expected_file_name))
