from django.apps import AppConfig
from books import image_cache


class BooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'books'

    def ready(self):
        super().ready()
        image_cache.sync_cache()
