import logging
import time
from typing import List, Optional

from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from google.oauth2 import service_account

from .models import RoyaltyRow

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


class BigQueryUploader:
    """
    Uploads royalty data to BigQuery.

    Authentication options:
    1. Service account JSON key file (for local development)
    2. Default credentials (for Cloud Functions with attached service account)

    Usage:
        # With explicit credentials file
        uploader = BigQueryUploader(
            project_id="my-project",
            dataset_id="royalties",
            table_id="findaway",
            credentials_path="/path/to/service-account.json"
        )

        # With default credentials (in Cloud Functions, project inferred)
        uploader = BigQueryUploader(
            dataset_id="royalties",
            table_id="findaway"
        )

        # Create or recreate the table
        uploader.create_table()

        # Upload rows
        uploader.upload_rows(rows)
    """

    # BigQuery schema matching RoyaltyRow dataclass
    SCHEMA = [
        bigquery.SchemaField("sale_month", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("source_file", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sales_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("royalty_rate", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("display_number", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("isbn", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("publisher", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("partner", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("promotion", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("sale_territory", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("currency", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dlp", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("price_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sales_qty", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("revenue", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("royalty_earned", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("less_distribution_fee", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("exchange_rate", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("royalty_payable_currency", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("royalty_payable", "FLOAT", mode="REQUIRED"),
    ]

    def __init__(
        self,
        dataset_id: str,
        table_id: str,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        """
        Initialize the BigQuery uploader.

        Args:
            dataset_id: BigQuery dataset ID.
            table_id: BigQuery table ID.
            project_id: GCP project ID. If None, inferred from environment.
            credentials_path: Path to service account JSON key file.
                              If None, uses Application Default Credentials.
        """
        self.dataset_id = dataset_id
        self.table_id = table_id

        self._client = self._build_client(project_id, credentials_path)
        self.project_id = self._client.project
        self.full_table_id = f"{self.project_id}.{dataset_id}.{table_id}"

    def _build_client(
        self, project_id: Optional[str], credentials_path: Optional[str]
    ) -> bigquery.Client:
        """Build the BigQuery client."""
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            return bigquery.Client(project=project_id, credentials=credentials)
        else:
            return bigquery.Client(project=project_id)

    def create_table(self, drop_if_exists: bool = False) -> None:
        """
        Create the table with the RoyaltyRow schema.

        Args:
            drop_if_exists: If True, drop the table first if it exists.
        """
        if drop_if_exists:
            self._client.delete_table(self.full_table_id, not_found_ok=True)

        table = bigquery.Table(self.full_table_id, schema=self.SCHEMA)
        self._client.create_table(table, exists_ok=True)

    def upload_rows(
        self,
        rows: List[RoyaltyRow],
        max_retries: int = 5,
        initial_delay: float = 1.0,
    ) -> int:
        """
        Upload rows to the BigQuery table with exponential backoff.

        Args:
            rows: List of RoyaltyRow objects to upload.
            max_retries: Maximum number of retry attempts.
            initial_delay: Initial delay in seconds between retries.

        Returns:
            Number of rows uploaded.

        Raises:
            Exception: If there are errors inserting rows after all retries.
        """
        if not rows:
            return 0

        # Convert RoyaltyRow objects to dicts for BigQuery
        rows_to_insert = [
            {
                "sale_month": row.sale_month.isoformat(),
                "source_file": row.source_file,
                "title": row.title,
                "sales_type": row.sales_type,
                "royalty_rate": row.royalty_rate,
                "display_number": row.display_number,
                "isbn": row.isbn,
                "publisher": row.publisher,
                "partner": row.partner,
                "promotion": row.promotion,
                "sale_territory": row.sale_territory,
                "currency": row.currency,
                "dlp": row.dlp,
                "price_type": row.price_type,
                "sales_qty": row.sales_qty,
                "revenue": row.revenue,
                "royalty_earned": row.royalty_earned,
                "less_distribution_fee": row.less_distribution_fee,
                "exchange_rate": row.exchange_rate,
                "royalty_payable_currency": row.royalty_payable_currency,
                "royalty_payable": row.royalty_payable,
            }
            for row in rows
        ]

        # Retry with exponential backoff in case table is not yet available
        delay = initial_delay
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                errors = self._client.insert_rows_json(
                    self.full_table_id, rows_to_insert
                )

                if errors:
                    raise Exception(f"Errors inserting rows into BigQuery: {errors}")

                return len(rows_to_insert)

            except NotFound as e:
                last_error = e
                if attempt < max_retries:
                    logging.warning(
                        f"Table not found (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

        raise Exception(
            f"Table {self.full_table_id} not available after {max_retries + 1} attempts"
        ) from last_error
