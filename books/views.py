from django.shortcuts import render, get_object_or_404

from .models import Book, Person, Tag


all_books = Book.objects
COLORS = [
        '/static/cover_templates/cover_templates_blue.jpeg',
        '/static/cover_templates/cover_templates_green.jpeg',
        '/static/cover_templates/cover_templates_grey.jpeg',
        '/static/cover_templates/cover_templates_purple.jpeg',
        '/static/cover_templates/cover_templates_red.jpeg',
        '/static/cover_templates/cover_templates_yellow.jpeg'
    ]

def index(request):
    """Index page, starting page"""
    # query all books from DB and order by date and by tag filter
    promoted_books = all_books.promoted().order_by('-added_at')

    # Getting all Tags and creating querystring objects for each to pass to template
    tags = Tag.objects.all()
    found_tag = {}
    tags_to_render = []
    for tag in tags:
        #checking if tag is assigned to any book, we don't show tags without books assigned
        if tag.tag.exists():
            found_tag['name']=tag.name
            found_tag['slug']=tag.slug
            found_tag['books']=all_books.filtered(tag=tag.name).order_by('-added_at')
            tags_to_render.append(found_tag.copy())

    context = {
        'promo_books': promoted_books,
        'tags_to_render': tags_to_render,
        'colors': COLORS
    }
    
    return render(request, 'books/index.html', context)

def books(request):
    """All books page"""
    sorted_books = all_books.order('title')
    tags = Tag.objects.all()

    req_tag = request.GET.get('books')

    if req_tag:
        if req_tag == 'Прапануем паслухаць':
            books_tag = all_books.promoted()
            tag_name = req_tag
        else:
            tag_name=tags.filter(slug=req_tag)[0].name
            books_tag = all_books.filtered(tag=tag_name)

        context = {
            'all_books': books_tag,
            'tag': tag_name,
            'colors': COLORS,
            'tags': tags
        }
    else:
        context = {
            'all_books': sorted_books,
            'colors': COLORS,
            'tags': tags
        }

    return render(request, 'books/all-books.html', context)

def book_detail(request, slug):
    """Detailed book page"""
    identified_book = get_object_or_404(Book, slug=slug)

    context = {
        'book': identified_book,
        'authors': identified_book.authors.all(),
        'narrations': identified_book.narration.all(),
        'tags': identified_book.tag.all(),
        'colors': COLORS
        
    }

    return render(request, 'books/book-detail.html', context)

def person_detail(request, slug):
    """Detailed book page"""
    identified_person = get_object_or_404(Person, slug=slug)

    # Prefetch all books in the relationships
    related_books=Person.objects.prefetch_related('authors','translators').filter(uuid=identified_person.uuid)

    # Select books for each relationship
    for person in related_books:
        author = person.authors.all()
        translator = person.translators.all()
        #TODO: need to find the way to show narrations now
        # for narration in person.narrator.all():
        #     narration

    # TODO: need to think how to refactor queries for less SQL calls:
    # TODO: we also need to change narrator DB access here to pass to the template
    # authors=Person.objects.prefetch_related('authors').all()
    # narrators=Person.objects.prefetch_related('authors').all()
    # translators=Person.objects.prefetch_related('authors').all()

    context = {
        'person': identified_person,
        'author': author,
        'translator': translator,
        #TODO: Need to find the way to show Narrations now
        # 'narrator': narrator,
        'colors': COLORS
    }

    return render(request, 'books/person.html', context)

def search(request):
    """Search results"""
    books = all_books.order('-added_at')

    # keywords in search field
    keywords = request.GET.get('search')

    if keywords:
        #Search by Book's title, russian translation of the title and books author name
        search_results = (all_books.filtered(title=keywords) | all_books.filtered(title_ru=keywords) | all_books.filtered(author=keywords)).distinct()

        context = {
            'books': search_results,
            'values': keywords,
            'colors': COLORS
        }

    else:
        context = {
            'books': books,
            'colors': COLORS
        }

    return render(request, 'books/search.html', context)