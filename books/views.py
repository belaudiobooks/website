from django.shortcuts import render, get_object_or_404

from .models import Book


def index(request):
    """Index page, starting page"""
    # query all books from DB and order by date and by promo filter
    all_books = Book.objects.all()
    latest_books = all_books.order_by('-added_at')[:4]
    filtered_books_promo = all_books.filter(promoted=True)
    
    return render(request, 'books/index.html', {
        'books': latest_books,
        'promo_books': filtered_books_promo
    })

def books(request):
    """All books page"""
    sorted_books = Book.objects.all().order_by('title')
    return render(request, 'books/all-books.html', {
        'all_books': sorted_books
    })

def book_detail(request, slug):
    """Detailed book page"""
    identified_book = get_object_or_404(Book, slug=slug)
    return render(request, 'books/book-detail.html', {
        'book': identified_book,
        'authors': identified_book.authors.all()
    })