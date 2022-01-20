from django.shortcuts import render, get_object_or_404

from .models import Book, Person
from .books_handler import BooksHandler

all_books = BooksHandler()

def index(request):
    """Index page, starting page"""
    # query all books from DB and order by date and by promo filter
    latest_books = all_books.order('-added_at',4)
    filtered_books_promo = all_books.filter_handler({'field':'promoted','value':True})
    filtered_books_tag = all_books.filter_handler({'field':'tag','value':'Дзіцячыя'})

    context = {
        'books': latest_books,
        'promo_books': filtered_books_promo,
        'len_promo': len(filtered_books_promo),
        'tag': filtered_books_tag
    }
    
    return render(request, 'books/index.html', context)

def books(request):
    """All books page"""
    sorted_books = all_books.order('title')

    tag = request.GET.get('books')

    if tag:
        books_tag = all_books.filter_handler({'field':'tag','value':tag})

        context = {
            'all_books': books_tag,
            'values': tag
        }

    else:
        context = {
            'all_books': sorted_books
        }

    return render(request, 'books/all-books.html', context)

def book_detail(request, slug):
    """Detailed book page"""
    identified_book = get_object_or_404(Book, slug=slug)

    context = {
        'book': identified_book,
        'authors': identified_book.authors.all()
    }

    return render(request, 'books/book-detail.html', context)

def person_detail(request, slug):
    """Detailed book page"""
    identified_person = get_object_or_404(Person, slug=slug)

    context = {
        'person': identified_person,
    }

    return render(request, 'books/person.html', context)

def search(request):
    """Search results"""
    books = all_books.order('-added_at')

    # keywords in search field
    keywords = request.GET.get('search')

    if keywords:
        search_results = (all_books.filter_handler({'field':'title','value':keywords}) | all_books.filter_handler({'field':'author','value':keywords})).distinct()

        context = {
            'books': search_results,
            'values': keywords
        }

    else:
        context = {
            'books': books
        }

    return render(request, 'books/search.html', context)