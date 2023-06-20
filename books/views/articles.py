'''
Views that render articles.
'''

from dataclasses import dataclass
from typing import List
from django import views
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

@dataclass
class Article:
    '''Data related to a single article.'''
    # Example: 'Як выкласці аўдыякнігу'
    title: str
    # Example: jak-vyklasci-audyjaknihu
    slug: str
    # Example: 'Гэта артыкула пра бла-бла'
    short_description: str
    # Example: how-to-publish-audiobook.html
    template: str


ARTICLES: List[Article] = [
    Article(
        title='Як выкласці аўдыякнігу',
        short_description=
        'Гайд пра тое, як лепей распаўсюдзіць аўдыякнігу на беларускай мове.',
        slug='jak-vyklasci-audyjaknihu',
        template='how-to-publish-audiobook.html'),
    Article(title='База даных audiobooks.by',
            short_description=
            'Дзе знайсці і як карыстацца базай даных сайта audiobooks.by',
            slug='baza-danych-audiobooksby',
            template='audiobooksby-database.html'),
    Article(title='Гайд па вокладках аўдыякніг',
            short_description=
            'Як зрабіць добрыя вокладкі аўдыякніг: фармат, памеры, змест.',
            slug='hajd-pa-vokladkach-audyjaknih',
            template='covers-guide.html'),
]


def redirect_to_first_article(request: HttpRequest) -> HttpRequest:
    '''Redirects to the first article'''
    return redirect(reverse('single-article', args=(ARTICLES[0].slug, )))


def single_article(request: HttpRequest, slug: str) -> HttpResponse:
    '''Serve an article'''
    for article in ARTICLES:
        if article.slug == slug:
            return render(request, f'books/articles/{article.template}', {
                'article': article,
                'all_articles': ARTICLES,
            })
    return views.defaults.page_not_found(request, None)