from datetime import date

from django.shortcuts import render

# dummy data for testing
all_books = [
    {
        "slug": "ivan_meleg",
        "image": "imeleg.png",
        "author": "Іван Мележ",
        "title": "Подых навальніцы",
        "genre": "Раман",
        "date": date(1986,3,2),
        "links": ('http://test.one', 'http://test.two'),
        "promoted": True,
        "content": """
            Lorem ipsum dolor sit ametsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n consectetur adipisicing elit. 
            Ipsam voluptasum dolor sit amet cosum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nnsectetur adipisicing elit. 
            Ipsam voluptatum ntum nam culpa qssum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum num dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nuos ab ansum dolorsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nimi, veritatis
        """,
        "annotation": """
            Lorem ipsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nam culpa quos ab animi, veritatis
        """
    },
    {
        "slug": "book-two",
        "image": "imeleg.png",
        "author": "Book 2",
        "title": "Title 2",
        "genre": "Раман",
        "date": date(1989,12,12),
        "links": ['http://test.one', 'http://test.two'],
        "promoted": False,
        "content": """
            Lorem ipsum dolor sit ametsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n consectetur adipisicing elit. 
            Ipsam voluptasum dolor sit amet cosum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nnsectetur adipisicing elit. 
            Ipsam voluptatum ntum nam culpa qssum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum num dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nuos ab ansum dolorsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nimi, veritatis
        """,
        "annotation": """
            Lorem ipsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nam culpa quos ab animi, veritatis
        """
    },
    {
        "slug": "this-book-three",
        "image": "imeleg.png",
        "author": "Book 3",
        "title": "Book 3 Title",
        "genre": "Раман",
        "date": date(1984,12,12),
        "links": ['http://test.one', 'http://test.two'],
        "promoted": True,
        "content": """
            Lorem ipsum dolor sit ametsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n consectetur adipisicing elit. 
            Ipsam voluptasum dolor sit amet cosum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nnsectetur adipisicing elit. 
            Ipsam voluptatum ntum nam culpa qssum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum num dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nuos ab ansum dolorsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nimi, veritatis
        """,
        "annotation": """
            Lorem ipsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nam culpa quos ab animi, veritatis
        """
    },
    {
        "slug": "book-four",
        "image": "imeleg.png",
        "author": "author book 4",
        "title": "Book 4 Title",
        "genre": "Раман",
        "date": date(1987,12,12),
        "links": ['http://test.one', 'http://test.two'],
        "promoted": False,
        "content": """
            Lorem ipsum dolor sit ametsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n consectetur adipisicing elit. 
            Ipsam voluptasum dolor sit amet cosum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nnsectetur adipisicing elit. 
            Ipsam voluptatum ntum nam culpa qssum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum num dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nuos ab ansum dolorsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum n sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nimi, veritatis
        """,
        "annotation": """
            Lorem ipsum dolor sit amet consectetur adipisicing elit. 
            Ipsam voluptatum nam culpa quos ab animi, veritatis
        """
    }
]

def get_date(book):
    """Get date helper"""
    return book.get('date')

def get_promoted(book):
    """Get promoted helper"""
    return book.get('promoted')

#sort by date
sorted_books = sorted(all_books, key=get_date)

def index(request):
    """Index page, starting page"""
    #filter by promoted
    filtered_books_promo = filter(get_promoted, all_books)
    # Sort by date and return latest 3
    latest_books = sorted_books[-4:]
    return render(request, 'books/index.html', {
        'books': latest_books,
        'promo_books': filtered_books_promo
    })

def books(request):
    """All books page"""
    return render(request, 'books/all-books.html', {
        'all_books': sorted_books
    })

def book_detail(request, slug):
    """Detailed book page"""
    book = next(book for book in all_books if book['slug'] ==  slug)
    return render(request, 'books/book-detail.html', {
        'book': book
    })