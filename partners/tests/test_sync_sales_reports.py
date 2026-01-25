import os
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TransactionTestCase, Client

from partners.models import SaleRecord
from partners.services.google_drive_fetcher import DriveFile


class TestSyncSalesReports(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        # Load test xlsx file content
        test_file = os.path.join(
            os.path.dirname(__file__),
            "data",
            "Findaway Belaudiobooks (2025-06 Digital Royalty).xlsx",
        )
        with open(test_file, "rb") as f:
            self.test_file_content = f.read()

    @patch("partners.jobs.GoogleDriveFetcher")
    @patch.dict(os.environ, {"GOOGLE_DRIVE_FOLDER_ID": "test-folder-id"})
    def test_sync_sales_reports_creates_records(self, mock_fetcher_class):
        # Set up mock
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.list_xlsx_files.return_value = [
            DriveFile(id="file-123", name="test-report.xlsx")
        ]
        mock_fetcher.download_file.return_value = self.test_file_content

        # Call the endpoint
        response = self.client.get("/partners/job/sync_sales_reports")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Sync complete", response.content.decode())

        # Verify records were created
        records = SaleRecord.objects.all()
        self.assertEqual(records.count(), 11)  # 4 retail + 5 subscription + 2 pool

        # Verify a specific record
        first_record = records.filter(title="Палёт над гняздом зязюлі").first()
        self.assertIsNotNone(first_record)
        self.assertEqual(first_record.month_of_sale, date(2025, 6, 1))
        self.assertEqual(first_record.source_file, "test-report.xlsx")
        self.assertEqual(first_record.drive_id, "file-123")
        self.assertEqual(first_record.sales_type, "Retail")
        self.assertEqual(first_record.isbn, "9798347944019")
        self.assertEqual(first_record.retailer, "Google Play")
        self.assertEqual(first_record.country, "PL")
        self.assertEqual(first_record.quantity, 1)
        self.assertEqual(first_record.amount_currency, "USD")
        self.assertEqual(first_record.amount, Decimal("4.8"))

    @patch("partners.jobs.GoogleDriveFetcher")
    @patch.dict(os.environ, {"GOOGLE_DRIVE_FOLDER_ID": "test-folder-id"})
    def test_sync_deletes_existing_records(self, mock_fetcher_class):
        # Create an existing record
        SaleRecord.objects.create(
            month_of_sale=date(2020, 1, 1),
            source_file="old-file.xlsx",
            drive_id="old-id",
            title="Old Record",
            sales_type="Retail",
            isbn="123",
            retailer="Old Retailer",
            country="US",
            quantity=1,
            amount_currency="USD",
            amount=Decimal("10.00"),
        )
        self.assertEqual(SaleRecord.objects.count(), 1)

        # Set up mock
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.list_xlsx_files.return_value = [
            DriveFile(id="file-123", name="test-report.xlsx")
        ]
        mock_fetcher.download_file.return_value = self.test_file_content

        # Call the endpoint
        response = self.client.get("/partners/job/sync_sales_reports")

        self.assertEqual(response.status_code, 200)

        # Old record should be deleted, only new records exist
        self.assertEqual(SaleRecord.objects.count(), 11)
        self.assertFalse(SaleRecord.objects.filter(title="Old Record").exists())

    @patch("partners.jobs.GoogleDriveFetcher")
    @patch.dict(os.environ, {"GOOGLE_DRIVE_FOLDER_ID": "test-folder-id"})
    def test_sync_with_no_files(self, mock_fetcher_class):
        # Set up mock to return no files
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_fetcher.list_xlsx_files.return_value = []

        response = self.client.get("/partners/job/sync_sales_reports")

        self.assertEqual(response.status_code, 200)
        self.assertIn("No xlsx files found", response.content.decode())

    def test_sync_without_env_var_returns_error(self):
        # Make sure env var is not set
        with patch.dict(os.environ, {}, clear=True):
            # Need to preserve other env vars Django needs
            response = self.client.get("/partners/job/sync_sales_reports")

        self.assertEqual(response.status_code, 500)
        self.assertIn("GOOGLE_DRIVE_FOLDER_ID", response.content.decode())
