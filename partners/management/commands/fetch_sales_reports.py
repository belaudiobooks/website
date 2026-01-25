"""
Django management command to fetch and parse royalty reports from Google Drive.

Usage:
    python manage.py fetch_sales_reports --credentials /path/to/service-account.json --folder FOLDER_ID
"""

from collections import defaultdict
from datetime import date
from typing import Dict, List

from django.core.management.base import BaseCommand

from partners.models import SaleRecord
from partners.parsers.findaway import parse_findaway_report
from partners.services.google_drive_fetcher import GoogleDriveFetcher


class Command(BaseCommand):
    help = "Fetch and parse royalty report files from Google Drive"

    def add_arguments(self, parser):
        parser.add_argument(
            "--credentials",
            required=True,
            help="Path to service account JSON key file",
        )
        parser.add_argument(
            "--folder",
            required=True,
            help="Google Drive folder ID",
        )
        parser.add_argument(
            "--samples",
            type=int,
            default=-1,
            help="Number of files to process (-1 or omit for all)",
        )

    def handle(self, *args, **options):
        fetcher = GoogleDriveFetcher(
            folder_id=options["folder"],
            credentials_path=options["credentials"],
        )

        self.stdout.write(f"Fetching .xlsx files from folder: {options['folder']}")
        self.stdout.write("")

        files = fetcher.list_xlsx_files()

        if not files:
            self.stdout.write("No .xlsx files found.")
            return

        self.stdout.write(f"Found {len(files)} file(s):")
        for f in files:
            self.stdout.write(f"  - {f.name}")
        self.stdout.write("")

        # Limit files if --samples is specified
        if options["samples"] >= 0:
            files = files[: options["samples"]]
            self.stdout.write(
                f"Processing {len(files)} file(s) (--samples={options['samples']})"
            )
            self.stdout.write("")

        # Parse all files and collect rows
        all_rows: List[SaleRecord] = []
        for f in files:
            self.stdout.write(f"Parsing: {f.name}...", ending=" ")
            content = fetcher.download_file(f.id)
            rows = parse_findaway_report(content, f.name, drive_id=f.id)
            all_rows.extend(rows)
            self.stdout.write(f"{len(rows)} rows")

        self.stdout.write("")
        self.stdout.write(f"Total rows parsed: {len(all_rows)}")
        self.stdout.write("")

        # Group by month and calculate stats
        stats_by_month: Dict[date, Dict] = defaultdict(
            lambda: {"count": 0, "amount": 0.0}
        )
        for row in all_rows:
            stats_by_month[row.month_of_sale]["count"] += 1
            stats_by_month[row.month_of_sale]["amount"] += float(row.amount)

        # Print per-month stats
        self.stdout.write("Per-month statistics:")
        self.stdout.write("-" * 45)
        self.stdout.write(f"{'Month':<12} {'Rows':>8} {'Amount':>12}")
        self.stdout.write("-" * 45)

        total_amount = 0.0
        for month in sorted(stats_by_month.keys()):
            stats = stats_by_month[month]
            month_str = month.strftime("%Y-%m")
            self.stdout.write(
                f"{month_str:<12} {stats['count']:>8} {stats['amount']:>12.2f} USD"
            )
            total_amount += stats["amount"]

        self.stdout.write("-" * 45)
        self.stdout.write(f"{'TOTAL':<12} {len(all_rows):>8} {total_amount:>12.2f} USD")
