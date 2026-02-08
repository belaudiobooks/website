from datetime import date
from decimal import Decimal

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from books.models import ISBN
from partners.models import Agreement, SaleRecord
from partners.tests.webdriver_test_case import WebdriverTestCase


class SalesPageTest(WebdriverTestCase):
    def setUp(self):
        super().setUp()
        fake = self.books_fake_data

        # Create two books with narrations
        self.book1 = fake.create_book_with_single_narration(
            title="First Book",
            authors=[fake.person_ales],
            narrators=[fake.person_bela],
        )
        self.book2 = fake.create_book_with_single_narration(
            title="Second Book",
            authors=[fake.person_viktar],
            narrators=[fake.person_volha],
        )

        self.narration1 = self.book1.narrations.first()
        self.narration2 = self.book2.narrations.first()

        # Create ISBNs for narrations
        self.isbn1 = ISBN.objects.create(
            code="1234567890123", narration=self.narration1
        )
        self.isbn2 = ISBN.objects.create(
            code="9876543210987", narration=self.narration2
        )

        # Create two agreements with different royalty rates
        self.agreement1 = Agreement.objects.create(
            partner=self.partner, royalty_percent=Decimal("50.00")
        )
        self.agreement1.narrations.add(self.narration1)

        self.agreement2 = Agreement.objects.create(
            partner=self.partner, royalty_percent=Decimal("25.00")
        )
        self.agreement2.narrations.add(self.narration2)

        # Create 4 sale records:
        # Book 1: November 2025 and December 2025
        # Book 2: January 2026 (two sales in same month)
        SaleRecord.objects.create(
            month_of_sale=date(2025, 11, 1),
            source_file="test.xlsx",
            drive_id="test_drive_id",
            title="First Book",
            sales_type="retail",
            isbn=self.isbn1,
            retailer="Test Retailer",
            quantity=10,
            amount_currency="USD",
            amount=Decimal("100.00"),
        )
        SaleRecord.objects.create(
            month_of_sale=date(2025, 12, 1),
            source_file="test.xlsx",
            drive_id="test_drive_id",
            title="First Book",
            sales_type="retail",
            isbn=self.isbn1,
            retailer="Test Retailer",
            quantity=5,
            amount_currency="USD",
            amount=Decimal("50.00"),
        )
        SaleRecord.objects.create(
            month_of_sale=date(2026, 1, 1),
            source_file="test.xlsx",
            drive_id="test_drive_id",
            title="Second Book",
            sales_type="retail",
            isbn=self.isbn2,
            retailer="Test Retailer",
            quantity=20,
            amount_currency="USD",
            amount=Decimal("200.00"),
        )
        SaleRecord.objects.create(
            month_of_sale=date(2026, 1, 1),
            source_file="test.xlsx",
            drive_id="test_drive_id",
            title="Second Book",
            sales_type="subscription",
            isbn=self.isbn2,
            retailer="Another Retailer",
            quantity=8,
            amount_currency="USD",
            amount=Decimal("80.00"),
        )

    def get_table_rows(self, view_mode="all-time"):
        """Parse table rows into list of dicts.

        Args:
            view_mode: One of 'all-time', 'yearly', or 'monthly'
        """
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#sales-table tbody tr")
        row_data = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if view_mode == "all-time":
                row_data.append(
                    {
                        "title": cells[0].text,
                        "quantity": cells[2].text,
                        "original_amount": cells[3].text,
                        "royalty_share": cells[4].text,
                        "payable_royalty": cells[5].text,
                    }
                )
            elif view_mode == "yearly":
                row_data.append(
                    {
                        "title": cells[0].text,
                        "year": cells[2].text,
                        "quantity": cells[3].text,
                        "original_amount": cells[4].text,
                        "royalty_share": cells[5].text,
                        "payable_royalty": cells[6].text,
                    }
                )
            else:  # monthly
                row_data.append(
                    {
                        "title": cells[0].text,
                        "year": cells[2].text,
                        "month": cells[3].text,
                        "quantity": cells[4].text,
                        "original_amount": cells[5].text,
                        "royalty_share": cells[6].text,
                        "payable_royalty": cells[7].text,
                    }
                )
        return row_data

    def get_totals(self):
        """Get totals from table footer."""
        total_quantity = self.driver.find_element(
            By.CSS_SELECTOR, "[data-test-id='total-quantity']"
        )
        total_payable = self.driver.find_element(
            By.CSS_SELECTOR, "[data-test-id='total-payable-royalty']"
        )
        return {"quantity": total_quantity.text, "payable_royalty": total_payable.text}

    def test_all_time_view_is_default_and_shows_two_rows(self):
        """All-time view should be the default and show 2 rows (one per book)."""
        self.login()
        self.driver.get(f"{self.live_server_url}/partners/{self.partner.id}/sales/")

        # Wait for DataTable to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#sales-table tbody tr"))
        )

        # Verify all-time is selected by default
        all_time_toggle = self.driver.find_element(By.ID, "view-all-time")
        self.assertTrue(all_time_toggle.is_selected())

        row_data = self.get_table_rows(view_mode="all-time")
        self.assertEqual(
            [
                {
                    "title": "First Book",
                    "quantity": "15",
                    "original_amount": "$150.00",
                    "royalty_share": "50%",
                    "payable_royalty": "$75.00",
                },
                {
                    "title": "Second Book",
                    "quantity": "28",
                    "original_amount": "$280.00",
                    "royalty_share": "25%",
                    "payable_royalty": "$70.00",
                },
            ],
            row_data,
        )

        self.assertEqual(
            {"quantity": "43", "payable_royalty": "$145.00"}, self.get_totals()
        )

    def test_monthly_view_shows_three_rows_with_correct_data(self):
        """Monthly view should show 3 rows (one per book per month)."""
        self.login()
        self.driver.get(f"{self.live_server_url}/partners/{self.partner.id}/sales/")

        # Wait for DataTable to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#sales-table tbody tr"))
        )

        # Switch to monthly view (click label, as Bootstrap hides the input)
        monthly_label = self.driver.find_element(
            By.CSS_SELECTOR, "label[for='view-monthly']"
        )
        monthly_label.click()

        # Wait for table to rebuild with 3 rows
        WebDriverWait(self.driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#sales-table tbody tr"))
            == 3
        )

        row_data = self.get_table_rows(view_mode="monthly")
        self.assertEqual(
            [
                {
                    "title": "Second Book",
                    "year": "2026",
                    "month": "Студзень",
                    "quantity": "28",
                    "original_amount": "$280.00",
                    "royalty_share": "25%",
                    "payable_royalty": "$70.00",
                },
                {
                    "title": "First Book",
                    "year": "2025",
                    "month": "Снежань",
                    "quantity": "5",
                    "original_amount": "$50.00",
                    "royalty_share": "50%",
                    "payable_royalty": "$25.00",
                },
                {
                    "title": "First Book",
                    "year": "2025",
                    "month": "Лістапад",
                    "quantity": "10",
                    "original_amount": "$100.00",
                    "royalty_share": "50%",
                    "payable_royalty": "$50.00",
                },
            ],
            row_data,
        )

        self.assertEqual(
            {"quantity": "43", "payable_royalty": "$145.00"}, self.get_totals()
        )

    def test_yearly_view_shows_two_rows_with_aggregated_data(self):
        """Yearly view should aggregate data by year, showing 2 rows."""
        self.login()
        self.driver.get(f"{self.live_server_url}/partners/{self.partner.id}/sales/")

        # Wait for DataTable to initialize
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#sales-table tbody tr"))
        )

        # Switch to yearly view (click label, as Bootstrap hides the input)
        yearly_label = self.driver.find_element(
            By.CSS_SELECTOR, "label[for='view-yearly']"
        )
        yearly_label.click()

        # Wait for table to rebuild - yearly view has 2 rows (one per year per book)
        # In this case: First Book 2025, Second Book 2026
        WebDriverWait(self.driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#sales-table tbody tr"))
            == 2
        )

        row_data = self.get_table_rows(view_mode="yearly")
        self.assertEqual(
            [
                {
                    "title": "Second Book",
                    "year": "2026",
                    "quantity": "28",
                    "original_amount": "$280.00",
                    "royalty_share": "25%",
                    "payable_royalty": "$70.00",
                },
                {
                    "title": "First Book",
                    "year": "2025",
                    "quantity": "15",
                    "original_amount": "$150.00",
                    "royalty_share": "50%",
                    "payable_royalty": "$75.00",
                },
            ],
            row_data,
        )

        self.assertEqual(
            {"quantity": "43", "payable_royalty": "$145.00"}, self.get_totals()
        )
