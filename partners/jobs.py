"""
Background jobs for the partners app.
"""

import gc
import logging
import os

from django.http import HttpRequest, HttpResponse

from books.models import ISBN
from partners.models import SaleRecord
from partners.parsers.findaway import parse_findaway_report
from partners.services.google_drive_fetcher import GoogleDriveFetcher

logger = logging.getLogger(__name__)


def sync_sales_reports(request: HttpRequest) -> HttpResponse:
    """
    HTTP endpoint that syncs royalty reports from Google Drive to the database.

    Fetches all xlsx files from the configured Google Drive folder, parses them,
    and saves all rows to the database (deleting existing records first).

    Environment variables:
        GOOGLE_DRIVE_FOLDER_ID: Google Drive folder ID containing xlsx reports

    Query parameters:
        samples: Optional int. Limit number of files to process (for testing).

    Returns:
        Response with summary of the sync operation.
    """
    logger.info("Starting sync_sales_reports job")

    # Read configuration from environment variables
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
    if not folder_id:
        logger.error("Missing GOOGLE_DRIVE_FOLDER_ID environment variable")
        return HttpResponse(
            "Missing GOOGLE_DRIVE_FOLDER_ID environment variable", status=500
        )

    logger.info(f"Configuration: folder={folder_id}")

    # Initialize Google Drive client (uses default credentials in production)
    logger.info("Initializing Google Drive fetcher")
    fetcher = GoogleDriveFetcher(folder_id=folder_id)

    # Fetch all xlsx files
    logger.info("Fetching xlsx files from Google Drive")
    files = fetcher.list_xlsx_files()
    logger.info(f"Found {len(files)} xlsx file(s)")

    # Limit files if "samples" param is provided (for testing)
    samples = request.GET.get("samples")
    if samples is not None:
        samples = int(samples)
        if samples >= 0:
            files = files[:samples]
            logger.info(f"Limiting to {len(files)} file(s) (samples={samples})")

    if not files:
        logger.info("No files to process, exiting")
        return HttpResponse("No xlsx files found in Google Drive folder.", status=200)

    # Delete existing records before inserting new ones
    deleted_count, _ = SaleRecord.objects.all().delete()
    logger.info(f"Deleted {deleted_count} existing SaleRecord(s)")

    # Parse all files and save to database
    total_rows = 0
    for f in files:
        logger.info(f"Downloading and parsing: {f.name}")
        content = fetcher.download_file(f.id)
        rows_with_isbns = parse_findaway_report(content, f.name, drive_id=f.id)
        del content  # Free file bytes before bulk insert
        logger.info(f"Parsed {len(rows_with_isbns)} row(s) from {f.name}")

        # Create ISBN objects and assign to SaleRecords
        rows = _create_isbns_and_assign(rows_with_isbns)

        # Bulk create records
        SaleRecord.objects.bulk_create(rows)
        total_rows += len(rows)
        logger.info(f"Saved {len(rows)} row(s) to database")
        del rows  # Free SaleRecord list
        del rows_with_isbns
        gc.collect()  # Force garbage collection

    summary = (
        f"Sync complete. Processed {len(files)} file(s), saved {total_rows} row(s)."
    )
    logger.info(summary)
    return HttpResponse(summary, status=200)


def _create_isbns_and_assign(
    rows_with_isbns: list[tuple[SaleRecord, str]],
) -> list[SaleRecord]:
    """Bulk create ISBN objects and assign them to SaleRecords.

    Args:
        rows_with_isbns: List of (SaleRecord, isbn_code) tuples.

    Returns:
        List of SaleRecords with isbn field populated.
    """
    # Collect unique ISBN codes (excluding empty strings)
    isbn_codes = {isbn_code for _, isbn_code in rows_with_isbns if isbn_code}

    if isbn_codes:
        # Fetch existing ISBNs
        existing_isbns = {
            isbn.code: isbn for isbn in ISBN.objects.filter(code__in=isbn_codes)
        }

        # Create missing ISBNs
        missing_codes = isbn_codes - existing_isbns.keys()
        if missing_codes:
            new_isbns = ISBN.objects.bulk_create(
                [ISBN(code=code) for code in missing_codes]
            )
            for isbn in new_isbns:
                existing_isbns[isbn.code] = isbn

        # Assign ISBN objects to SaleRecords
        for sale_record, isbn_code in rows_with_isbns:
            if isbn_code:
                sale_record.isbn = existing_isbns[isbn_code]

    return [sale_record for sale_record, _ in rows_with_isbns]
