""" Integration with livelib mobile API.

Module responsible for integration with https://livelib.ru/ mobile API
and provides functions:
    * search books with reviews by text query (book name or author name or both)

Typical usage example:
    books = search_books_with_reviews("вершы")

"""
import requests
import json
import math

REQUIRED_HEADERS = {
    "Host": "www.livelib.ru",
    "Accept-Language": "en-US;q=1.0, ru-US;q=0.9, be-US;q=0.8",
    "Accept": "*/*",
    "Connection": "keep-alive",
    "Accept-Encoding": "gzip;q=1.0, compress;q=0.5",
    "User-Agent": "LiveLib/3.24.5 (ru.livelib.LiveLib; build:3.24.5; iOS 16.5.1) Alamofire/3.24.5"
}

SEARCH_PAGE_SIZE = 100


def _generate_session_guid():
    init_session_response = requests.get(
        url="https://www.livelib.ru/apiapp/v2.0/appsessions/me",
        headers=REQUIRED_HEADERS,
        params={
            'andyll': 'and7mpp4ss',
            'fields': 'guid'
        }
    )
    if init_session_response.status_code > 299:
        raise RuntimeError(f"Failed to start new livelib session, {init_session_response.text}, " +
                           f"response status: {init_session_response.status_code}")
    guid = json.loads(init_session_response.text).get("data").get("guid")
    return guid


def _get_another_page(query_text, session_token, start_from=1):
    search_response = requests.get(
        url="https://www.livelib.ru/apiapp/v2.0/search/books",
        headers=REQUIRED_HEADERS,
        params={
            'andyll': 'and7mpp4ss',
            'fields': 'author_id,author_name,avg_mark,id,count_reviews,is_work,name,pic_200,share_url(share_url),user_book_partial(book_read,rating)',
            'count': SEARCH_PAGE_SIZE,
            'start': start_from,
            'q': query_text.lower(),
            'app_session_guid': session_token
        }
    )
    if search_response.status_code > 299:
        raise RuntimeError(f"Failed to find book in livelib by title, {search_response.text}, " +
                           f"response status: {search_response.status_code}")
    body = json.loads(search_response.text)
    if body.get('status').get('code') > 299:
        raise RuntimeError(f"Failed to find book in livelib by title, {body}, " +
                           f"response status: {body.get('status').get('code')}")
    return body


def _find_books_by_title(query_text):
    session_token = _generate_session_guid()
    first_page = _get_another_page(query_text, session_token)
    pages = math.ceil(first_page.get('count') / SEARCH_PAGE_SIZE)
    if pages > 1:
        results = list(first_page.get('data'))
        for i in range(1, pages):
            page = _get_another_page(query_text, session_token, start_from=i + 1)
            results = results + page.get('data')
        return results
    else:
        return first_page.get('data')


def search_books_with_reviews(search_request_text):
    """
    Method returns result of search books having reviews on livelib.ru
    Example:
    [{
        "name": "Вершы і паэмы (сборник)",
        "author_name": "Янка Купала",
        "cover_image": "https://s1.livelib.ru/boocover/1001598084/200/50b7/boocover.jpg",
        "url": "https://www.livelib.ru/book/1001598084-vershy-i-paemy-sbornik-yanka-kupala"
    }]
    """
    results = []
    books = _find_books_by_title(search_request_text)
    for book in books:
        if book.get('count_reviews') and book.get('count_reviews') > 0:
            results.append(
                {
                    'name': book.get('name'),
                    'author_name': book.get('author_name'),
                    'cover_image': book.get('pic_200'),
                    'url': book.get('share_url').get('share_url')
                }
            )
    return results
