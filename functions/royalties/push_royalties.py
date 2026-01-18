"""
Cloud Function to sync royalty reports from Google Drive to BigQuery.

Environment variables:
    BIGQUERY_DATASET_ID: BigQuery dataset ID
    BIGQUERY_TABLE_ID: BigQuery table ID
    GOOGLE_DRIVE_FOLDER_ID: Google Drive folder ID containing xlsx reports
"""

import logging
import os

import functions_framework
from flask import Request, Response

from .bigquery_uploader import BigQueryUploader
from .google_drive_fetcher import GoogleDriveFetcher
from .parse_findaway_report import parse_findaway_report

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


@functions_framework.http
def push_royalties(request: Request) -> Response:
    """
    HTTP Cloud Function that syncs royalty reports from Google Drive to BigQuery.

    Fetches all xlsx files from the configured Google Drive folder, parses them,
    and uploads all rows to BigQuery (recreating the table each time).

    Query parameters:
        samples: Optional int. Limit number of files to process (for testing).

    Returns:
        Response with summary of the sync operation.
    """
    logging.info("Starting push_royalties function")

    # Read configuration from environment variables
    required_vars = [
        "BIGQUERY_DATASET_ID",
        "BIGQUERY_TABLE_ID",
        "GOOGLE_DRIVE_FOLDER_ID",
    ]
    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    dataset_id = os.environ["BIGQUERY_DATASET_ID"]
    table_id = os.environ["BIGQUERY_TABLE_ID"]
    folder_id = os.environ["GOOGLE_DRIVE_FOLDER_ID"]

    logging.info(
        f"Configuration: dataset={dataset_id}, table={table_id}, folder={folder_id}"
    )

    # Initialize clients (uses default credentials in Cloud Functions)
    logging.info("Initializing Google Drive fetcher")
    fetcher = GoogleDriveFetcher(folder_id=folder_id)

    logging.info("Initializing BigQuery uploader")
    uploader = BigQueryUploader(
        dataset_id=dataset_id,
        table_id=table_id,
    )

    # Recreate the table
    logging.info(f"Recreating table {uploader.full_table_id}")
    uploader.create_table(drop_if_exists=True)

    # Fetch all xlsx files
    logging.info("Fetching xlsx files from Google Drive")
    files = fetcher.list_xlsx_files()
    logging.info(f"Found {len(files)} xlsx file(s)")

    # Limit files if "samples" param is provided (for testing)
    samples = request.args.get("samples", type=int)
    if samples is not None and samples >= 0:
        files = files[:samples]
        logging.info(f"Limiting to {len(files)} file(s) (samples={samples})")

    if not files:
        logging.info("No files to process, exiting")
        return Response("No xlsx files found in Google Drive folder.", status=200)

    # Parse all files and collect rows
    all_rows = []
    uploaded_count = 0
    for f in files:
        logging.info(f"Downloading and parsing: {f.name}")
        content = fetcher.download_file(f.id)
        rows = parse_findaway_report(content, f.name)
        logging.info(f"Parsed {len(rows)} row(s) from {f.name}")
        # Upload to BigQuery
        logging.info(f"Uploading {len(rows)} row(s) to BigQuery")
        uploaded_count = uploaded_count + uploader.upload_rows(rows)
        logging.info(f"Successfully uploaded {uploaded_count} row(s)")
        all_rows.extend(rows)

    logging.info(f"Total rows parsed: {len(all_rows)}")

    summary = (
        f"Sync complete. "
        f"Processed {len(files)} file(s), "
        f"uploaded {uploaded_count} row(s) to {uploader.full_table_id}"
    )

    logging.info(summary)
    return Response(summary, status=200)
