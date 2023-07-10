from django.urls import path
from books.views import stats, catalog, book, person, support, articles, publisher

urlpatterns = [
    path('', catalog.index, name='index'),
    path('catalog', catalog.catalog, name='catalog-all-books'),
    path('catalog/<slug:tag_slug>', catalog.catalog, name='catalog-for-tag'),

    path('books/<slug:slug>', book.book_detail, name='book-detail-page'),
    path('person/<slug:slug>', person.person_detail, name='person-detail-page'),
    path('publisher/<slug:slug>', publisher.publisher_detail, name='publisher-detail-page'),

    path('about', stats.about, name='about'),
    path('stats/birthdays', stats.birthdays),
    path('stats/digest', stats.digest),

    path('articles', articles.redirect_to_first_article, name='all-articles'),
    path('articles/<slug:slug>', articles.single_article, name='single-article'),

    path('search', support.search, name='search'),
    path('push_data_to_algolia', support.push_data_to_algolia),
    path("404", support.page_not_found),
    path('robots.txt', support.robots_txt),
    path('sitemap.txt', support.sitemap),
    path('data.json', support.get_data_json),
    path('generate_data_json', support.generate_data_json),
    path('update_read_by_author_tag', support.update_read_by_author_tag),
    path('markdown_preview', support.markdown_to_html)
]
