from django.db import models


class BookManager(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related('authors')

    def order(self, field, *args):
        if args:
            count = args[0]
            return self.order_by(field)[:count]
        else:
            return self.order_by(field)

    def promoted(self, **kwargs):
        # the method accepts **kwargs, so that it is possible to filter
        # promoted books
        # i.e: Book.objects.promoted(insertion_date__gte=datetime.now)
        return self.filter(promoted=True, **kwargs)

    def handle_filter(self, field: str, value: str) -> None:
        _handler = self.FIELD_MAPPING.get(field)
        # handle filter and run the function with filter field and value:
        return _handler(self, value)

    def filtered(self, **kwargs) -> None:
        [[field, value]] = kwargs.items()
        # validate input
        return self.handle_filter(field, value)

    def _handle_title(self, value: str) -> None:
        return self.filter(title__icontains=value)

    def _handle_title_ru(self, value: str) -> None:
        return self.filter(title_ru__icontains=value)

    def _handle_author(self, value: str) -> None:
        return self.filter(authors__name__icontains=value)

    def _handle_tag(self, value: str) -> None:
        return self.filter(tag__name__icontains=value)

    def _handle_promoted(self, value: str) -> None:
        return self.filter(promoted=value)

    FIELD_MAPPING = {
        'title': _handle_title,
        'title_ru': _handle_title_ru,
        'author': _handle_author,
        'tag': _handle_tag,
        'promoted': _handle_promoted
    }