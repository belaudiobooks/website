from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class RoyaltyRow:
    """Represents a single row from a Findaway royalty report."""

    # Metadata inferred during parsing
    sale_month: date  # First day of the sale month (e.g., 2025-06-01 for June 2025)
    source_file: str  # XLSX filename the row was parsed from

    # Fields from the report
    title: str
    sales_type: str
    royalty_rate: Optional[float]
    display_number: str
    isbn: str
    publisher: str
    partner: str
    promotion: Optional[str]
    sale_territory: str
    currency: str
    dlp: float  # Digital List Price
    price_type: str
    sales_qty: int
    revenue: Optional[float]
    royalty_earned: float
    less_distribution_fee: float
    exchange_rate: Optional[float]
    royalty_payable_currency: str
    royalty_payable: float
