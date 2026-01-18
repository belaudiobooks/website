#!/usr/bin/env python3
"""
Local script to test fetching and parsing royalty reports from Google Drive.

Usage:
    python -m royalties.run_local --credentials /path/to/service-account.json --folder FOLDER_ID
"""

import argparse
from collections import defaultdict
from datetime import date
from typing import Dict, List

from .google_drive_fetcher import GoogleDriveFetcher
from .models import RoyaltyRow
from .parse_findaway_report import parse_findaway_report


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and parse royalty report files from Google Drive"
    )
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
    args = parser.parse_args()

    fetcher = GoogleDriveFetcher(
        folder_id=args.folder,
        credentials_path=args.credentials,
    )

    print(f"Fetching .xlsx files from folder: {args.folder}")
    print()

    files = fetcher.list_xlsx_files()

    if not files:
        print("No .xlsx files found.")
        return

    print(f"Found {len(files)} file(s):")
    for f in files:
        print(f"  - {f.name}")
    print()

    # Limit files if --samples is specified
    if args.samples >= 0:
        files = files[: args.samples]
        print(f"Processing {len(files)} file(s) (--samples={args.samples})")
        print()

    # Parse all files and collect rows
    all_rows: List[RoyaltyRow] = []
    for f in files:
        print(f"Parsing: {f.name}...", end=" ")
        content = fetcher.download_file(f.id)
        rows = parse_findaway_report(content, f.name)
        all_rows.extend(rows)
        print(f"{len(rows)} rows")

    print()
    print(f"Total rows parsed: {len(all_rows)}")
    print()

    # Group by month and calculate stats
    stats_by_month: Dict[date, Dict] = defaultdict(
        lambda: {"count": 0, "royalties": 0.0}
    )
    for row in all_rows:
        stats_by_month[row.sale_month]["count"] += 1
        stats_by_month[row.sale_month]["royalties"] += row.royalty_payable

    # Print per-month stats
    print("Per-month statistics:")
    print("-" * 45)
    print(f"{'Month':<12} {'Rows':>8} {'Royalties':>12}")
    print("-" * 45)

    total_royalties = 0.0
    for month in sorted(stats_by_month.keys()):
        stats = stats_by_month[month]
        month_str = month.strftime("%Y-%m")
        print(f"{month_str:<12} {stats['count']:>8} {stats['royalties']:>12.2f} USD")
        total_royalties += stats["royalties"]

    print("-" * 45)
    print(f"{'TOTAL':<12} {len(all_rows):>8} {total_royalties:>12.2f} USD")


if __name__ == "__main__":
    main()
