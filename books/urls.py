from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('books', views.books, name='books'),
    path('books/<slug:slug>', views.book_detail, name='book-detail-page'),
    path('person/<slug:slug>', views.person_detail, name='person-detail-page'),
    path('search', views.search, name='search'),
    path('about', views.about, name='about')
]