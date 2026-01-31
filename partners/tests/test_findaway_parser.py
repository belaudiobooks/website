import os
from datetime import date
from decimal import Decimal

from django.test import TestCase

from partners.parsers.findaway import parse_findaway_report


class TestParseFindawayReport(TestCase):
    def test_parse_report(self):
        # Load test file
        test_file = os.path.join(
            os.path.dirname(__file__),
            "data",
            "Findaway Belaudiobooks (2025-06 Digital Royalty).xlsx",
        )
        with open(test_file, "rb") as f:
            content = f.read()

        filename = "Findaway Belaudiobooks (2025-06 Digital Royalty).xlsx"
        drive_id = "test_drive_id"
        rows_with_isbns = parse_findaway_report(content, filename, drive_id)

        month_of_sale = date(2025, 6, 1)

        # Expected data: (title, sales_type, isbn, retailer, country, quantity, amount_currency, amount)
        expected_rows = [
            # Retail (4 rows)
            (
                "Палёт над гняздом зязюлі",
                "Retail",
                "9798347944019",
                "Google Play",
                "PL",
                1,
                "USD",
                Decimal("4.8"),
            ),
            (
                "Пасажыры карабля Тэсея",
                "Retail",
                "9798882408120",
                "Spotify",
                "US",
                1,
                "USD",
                Decimal("5"),
            ),
            (
                "Па той бок тэлеэкрана",
                "Retail",
                "9798882395345",
                "Google Play",
                "RU",
                1,
                "USD",
                Decimal("0"),
            ),
            (
                "Па што ідзеш, воўча?",
                "Retail",
                "9798318257742",
                "Google Play",
                "PL",
                1,
                "USD",
                Decimal("0"),
            ),
            # Subscription (5 rows)
            (
                "Адвечным шляхам",
                "Subscription-Credit Based",
                "9798368900551",
                "Audiobooks.com",
                "DE",
                1,
                "USD",
                Decimal("0"),
            ),
            (
                "Апошнія сведкі",
                "Subscription-Credit Based",
                "9798368936024",
                "Audiobooks.com",
                "MY",
                1,
                "USD",
                Decimal("0"),
            ),
            (
                "Малая падарожная кніга па Горадзе СОНца",
                "Subscription-Credit Based",
                "9798868756849",
                "Audiobooks.com",
                "SE",
                1,
                "USD",
                Decimal("2.24"),
            ),
            (
                "Метод Мацкевича",
                "Subscription-Credit Based",
                "9798368927299",
                "Audiobooks.com",
                "GR",
                1,
                "USD",
                Decimal("0"),
            ),
            (
                "Мёртвым не баліць",
                "Subscription-Credit Based",
                "9798868712531",
                "Audiobooks.com",
                "US",
                1,
                "USD",
                Decimal("0"),
            ),
            # Pool (2 rows)
            (
                "PR: как строить коммуникацию в публичном пространстве",
                "Pool",
                "9798368927589",
                "Spotify",
                "FR",
                0,
                "USD",
                Decimal("0.04"),
            ),
            (
                "Апошняя кніга пана А.",
                "Pool",
                "9781669686163",
                "Spotify",
                "DE",
                0,
                "USD",
                Decimal("0.2"),
            ),
        ]

        self.assertEqual(len(rows_with_isbns), len(expected_rows))

        for i, ((row, isbn_code), expected) in enumerate(
            zip(rows_with_isbns, expected_rows)
        ):
            (
                title,
                sales_type,
                expected_isbn,
                retailer,
                country,
                quantity,
                amount_currency,
                amount,
            ) = expected
            self.assertEqual(
                row.month_of_sale, month_of_sale, f"Row {i}: month_of_sale mismatch"
            )
            self.assertEqual(
                row.source_file, filename, f"Row {i}: source_file mismatch"
            )
            self.assertEqual(row.drive_id, drive_id, f"Row {i}: drive_id mismatch")
            self.assertEqual(row.title, title, f"Row {i}: title mismatch")
            self.assertEqual(
                row.sales_type, sales_type, f"Row {i}: sales_type mismatch"
            )
            self.assertEqual(isbn_code, expected_isbn, f"Row {i}: isbn mismatch")
            self.assertEqual(row.retailer, retailer, f"Row {i}: retailer mismatch")
            self.assertEqual(row.country, country, f"Row {i}: country mismatch")
            self.assertEqual(row.quantity, quantity, f"Row {i}: quantity mismatch")
            self.assertEqual(
                row.amount_currency,
                amount_currency,
                f"Row {i}: amount_currency mismatch",
            )
            self.assertEqual(row.amount, amount, f"Row {i}: amount mismatch")

    def test_parse_report_with_mismatched_net_amount(self):
        """Test that parsing fails when row amounts don't match Net Amount."""
        test_file = os.path.join(
            os.path.dirname(__file__),
            "data",
            "Bad Report.xlsx",
        )
        with open(test_file, "rb") as f:
            content = f.read()

        with self.assertRaises(ValueError) as context:
            parse_findaway_report(content, "Bad Report.xlsx")

        self.assertEqual(
            str(context.exception),
            "Amount mismatch in 'Bad Report.xlsx': "
            "sum of rows is 12.28, expected Net Amount is 24.28",
        )
