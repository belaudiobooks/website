from books.models import Book
from typing import Any, Dict


class BooksHandler:
    
    def __init__(self):
        self.books = Book.objects.all().prefetch_related('authors')
    
    def order(self, field, *args):
        if args:
            count = args[0]
            return_books = self.books.order_by(field)[:count]
        else:
            return_books = self.books.order_by(field)
 
        return return_books

    def handle_filter(self, field: str, value: str) -> None:
        _handler = self.FIELD_MAPPING.get(field)
        # handle filter and run the function with filter field and value:
        return _handler(value)

    def filter_handler(self, request: Dict[str, Any]) -> None:
        field = request.get("field")
        value = request.get("value")
        # validate input
        return self.handle_filter(field, value)
            
    def _handle_promoted(value: str) -> None:
        return_books = Book.objects.all().filter(promoted=value)
        
        return return_books

    def _handle_title(value: str) -> None:
        return_books = Book.objects.all().filter(title__icontains=value)
        
        return return_books

    def _handle_author(value: str) -> None:
        return_books = Book.objects.all().filter(authors__name__icontains=value)
        
        return return_books

    def _handle_tag(value: str) -> None:
        return_books = Book.objects.all().filter(tag__name__icontains=value)
        
        return return_books

    FIELD_MAPPING = {
        "promoted": _handle_promoted,
        "title": _handle_title,
        "author": _handle_author,
        'tag': _handle_tag
    }