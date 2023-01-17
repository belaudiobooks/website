from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('catalog', views.catalog, name='catalog-all-books'),
    path('catalog/<slug:slug>', views.catalog, name='catalog-for-tag'),
    path('books/<slug:slug>', views.book_detail, name='book-detail-page'),
    path('person/<slug:slug>', views.person_detail, name='person-detail-page'),
    path('search', views.search, name='search'),
    path('about', views.about, name='about'),
    path('push_data_to_algolia', views.push_data_to_algolia),
    path("404", views.page_not_found),
    path('robots.txt', views.robots_txt),
    path('sitemap.txt', views.sitemap),
    path('articles', views.redirect_to_first_article, name='all-articles'),
    path('articles/<slug:slug>', views.single_article, name='single-article'),
    path('data.json', views.get_data_json),
    path('generate_data_json', views.generate_data_json),
    path('update_read_by_author_tag', views.update_read_by_author_tag)
]
