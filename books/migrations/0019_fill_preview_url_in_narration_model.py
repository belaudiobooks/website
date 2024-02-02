# Manually writen SQL migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0018_narration_preview_url"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                """
            UPDATE books_narration
            SET preview_url = (
                SELECT preview_url
                FROM books_book
                WHERE uuid = book_id
            )
            WHERE book_id IN (
                SELECT book_id
                FROM books_narration
                GROUP BY book_id
                HAVING COUNT(*) = 1
            );
            """
            ],
            reverse_sql=[],
        ),
    ]
