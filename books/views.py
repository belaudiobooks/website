from django.shortcuts import render, get_object_or_404

from .models import Book, Person


all_books = Book.objects

def index(request):
    """Index page, starting page"""
    # query all books from DB and order by date and by tag filter
    promoted_books = all_books.promoted().order_by('-added_at')[:6]
    tag_modern = all_books.filtered(tag='Сучасныя').order_by('-added_at')[:6]
    tag_kids = all_books.filtered(tag='Дзіцячыя').order_by('-added_at')[:6]
    tag_classic = all_books.filtered(tag='Класічныя').order_by('-added_at')[:6]
    tag_foreign = all_books.filtered(tag='Замежныя').order_by('-added_at')[:6]

    context = {
        'promo_books': promoted_books,
        'tag_modern': tag_modern,
        'tag_kids': tag_kids,
        'tag_classic': tag_classic,
        'tag_foreign': tag_foreign
    }
    
    return render(request, 'books/index.html', context)

def books(request):
    """All books page"""
    sorted_books = all_books.order('title')

    req_tag = request.GET.get('books')

    if req_tag:
        if req_tag == 'Прапануем паслухаць':
            books_tag = all_books.promoted()
        else:
            books_tag = all_books.filtered(tag=req_tag)

        context = {
            'all_books': books_tag,
            'tag': req_tag
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
        'authors': identified_book.authors.all(),
        'translators': identified_book.translators.all(),
        'narrators': identified_book.narrators.all(),
        'tags': identified_book.tag.all()
        
    }

    return render(request, 'books/book-detail.html', context)

def person_detail(request, slug):
    """Detailed book page"""
    identified_person = get_object_or_404(Person, slug=slug)

    # Prefetch all books in the relationships
    related_books=Person.objects.prefetch_related('authors','translators','narrators').filter(uuid=identified_person.uuid)

    # Select books for each relationship
    for person in related_books:
        author = person.authors.all()
        translator = person.translators.all()
        narrator = person.narrators.all()

    # TODO: need to think how to refactor queries for less SQL calls:
    # authors=Person.objects.prefetch_related('authors').all()
    # narrators=Person.objects.prefetch_related('authors').all()
    # translators=Person.objects.prefetch_related('authors').all()

    context = {
        'person': identified_person,
        'author': author,
        'translator': translator,
        'narrator': narrator
    }

    return render(request, 'books/person.html', context)

def search(request):
    """Search results"""
    books = all_books.order('-added_at')

    # keywords in search field
    keywords = request.GET.get('search')

    if keywords:
        search_results = (all_books.filtered(title=keywords) | all_books.filtered(author=keywords)).distinct()

        context = {
            'books': search_results,
            'values': keywords
        }

    else:
        context = {
            'books': books
        }

    return render(request, 'books/search.html', context)