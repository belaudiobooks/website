from django.shortcuts import render, get_object_or_404

from .models import Book, Person


def index(request):
    """Index page, starting page"""
    # query all books from DB and order by date and by promo filter
    all_books = Book.objects.all()
    latest_books = all_books.order_by('-added_at')[:4]
    filtered_books_promo = all_books.filter(promoted=True)

    context = {
        'books': latest_books,
        'promo_books': filtered_books_promo
    }
    
    return render(request, 'books/index.html', context)

def books(request):
    """All books page"""
    sorted_books = Book.objects.all().order_by('title')

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
    books = Book.objects.all().order_by('-added_at')
    
    # keywords in search field
    keywords = request.GET['search']
    if keywords:
        search_results = (books.filter(title__icontains=keywords) | books.filter(authors__name__icontains=keywords)).distinct()

        context = {
            'books': search_results
        }

    else:
        context = {
            'books': books
        }

    return render(request, 'books/search.html', context)