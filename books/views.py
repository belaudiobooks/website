from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from .models import Book, Person, Tag

all_books = Book.objects


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
            found_tag['name'] = tag.name
            found_tag['slug'] = tag.slug
            found_tag['books'] = all_books.filtered(
                tag=tag.name).order_by('-added_at')
            tags_to_render.append(found_tag.copy())

    context = {
        'promo_books': promoted_books,
        'tags_to_render': tags_to_render,
    }

    return render(request, 'books/index.html', context)


def books(request):
    """All books page"""
    sorted_books = all_books.order('title')

    paginator = Paginator(sorted_books, 16)
    page = request.GET.get('page')
    paged_books = paginator.get_page(page)

    tags = Tag.objects.all()

    req_tag = request.GET.get('books')

    if req_tag:
        if req_tag == 'Прапануем паслухаць':
            books_tag = all_books.promoted()
            tag_name = req_tag
        else:
            tag_name = tags.filter(slug=req_tag)[0].name
            books_tag = all_books.filtered(tag=tag_name)

        context = {
            'all_books': books_tag,
            'tag': tag_name,
            'tags': tags,
        }
    else:
        context = {
            'all_books': paged_books,
            'tags': tags,
        }

    return render(request, 'books/all-books.html', context)


def book_detail(request, slug):
    """Detailed book page"""
    identified_book = get_object_or_404(Book, slug=slug)

    context = {
        'book': identified_book,
        'authors': identified_book.authors.all(),
        'translators': identified_book.translators.all(),
        'narrations': identified_book.narrations.all(),
        'tags': identified_book.tag.all(),
    }

    return render(request, 'books/book-detail.html', context)


def person_detail(request, slug):
    """Detailed book page"""

    narrated_books = []
    # TODO: remove it later if all good
    # identified_person = get_object_or_404(Person, slug=slug)

    # Prefetch all books in the relationships
    person = Person.objects.prefetch_related(
        'books_authored', 'books_translated',
        'narrations').filter(slug=slug).first()

    if person:
        author = person.books_authored.all()
        translator = person.books_translated.all()
        narrations = person.narrations.all()

        [narrated_books.append(item.book) for item in narrations]

        context = {
            'person': person,
            'author': author,
            'translator': translator,
            'narrations': narrated_books,
        }

        return render(request, 'books/person.html', context)

    else:
        pass  #TODO: implement 404 page


def search(request):
    """Search results"""
    books = all_books.order('-added_at')

    # keywords in search field
    keywords = request.GET.get('search')

    if keywords:
        #Search by Book's title, russian translation of the title and books author name
        search_results = (all_books.filtered(title=keywords)
                          | all_books.filtered(title_ru=keywords)
                          | all_books.filtered(author=keywords)).distinct()

        context = {
            'books': search_results,
            'values': keywords,
        }

    else:
        context = {
            'books': books,
        }

    return render(request, 'books/search.html', context)


def about(request):
    """About us page containing info about the website and the team."""
    people = [
        ('Мікіта', 'images/member-mikita.jpg'),
        ('Яўген', 'images/member-jauhen.jpg'),
        ('Павал', 'images/member-paval.jpg'),
        ('Алесь', 'images/member-ales.jpg'),
        ('Наста', 'images/member-nasta.jpg'),
        ('Алёна', 'images/member-alena.jpg'),
        ('Юра', 'images/member-jura.jpg'),
        ('Андрэй', 'images/member-andrey.jpg'),
    ]
    context = {'team_members': people}
    return render(request, 'books/about.html', context)