from books.models import Book


class BooksHandler:

    def __init__(self):
        self.books = Book.objects.all().prefetch_related('authors')
    
    def order(self, field, *args):
        if args:
            count = args[0]
            return_books = self.books.order_by(f'-{field}')[:count]
        else:
            return_books = self.books.order_by(f'-{field}')
 
        return return_books

#need to find better way to filter books, right now below is working but making to many SQL queries
    # def filter_title(value):
    #     return_books = Book.objects.all().filter(title__icontains=value)
    
    #     return return_books

    # def filter_promoted(value):
    #     return_books = Book.objects.all().filter(promoted=value)
        
    #     return return_books

    # def filters(field,value):
    #     switch = {
    #         'title':filter_title(value),
    #         'promoted':filter_promoted(value)
    #     }

    #     return switch.get(field,'No such field')