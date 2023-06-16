# Manually writen SQL migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_narration_duration_sec'),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE public.books_narration
            SET duration_sec = (
                SELECT duration_sec
                FROM public.books_book
                WHERE uuid = book_id
            )
            WHERE book_id IN (
                SELECT book_id
                FROM public.books_narration
                GROUP BY book_id
                HAVING COUNT(*) = 1
            );
            """
        ),
    ]
