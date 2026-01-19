# Manually writen SQL migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0002_narration_duration"),
    ]

    operations = [
        migrations.RunSQL(
            sql=["""
            UPDATE books_narration
            SET duration = (
                SELECT duration_sec
                FROM books_book
                WHERE uuid = book_id
            )
            WHERE book_id IN (
                SELECT book_id
                FROM books_narration
                GROUP BY book_id
                HAVING COUNT(*) = 1
            );
            """],
            reverse_sql=[],
        ),
    ]
