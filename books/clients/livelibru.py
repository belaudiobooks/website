import requests
import urllib
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


def _generate_session_guid():
    init_session_response = requests.get(
        url="https://www.livelib.ru/apiapp/v2.0/appsessions/me?andyll=and7mpp4ss&fields=guid",
        headers=REQUIRED_HEADERS
    )
    if init_session_response.status_code > 299:
        raise RuntimeError(f"Filed to start new livelib session, {init_session_response.text}, " +
                           f"response status: {init_session_response.status_code}")
    guid = json.loads(init_session_response.text).get("data").get("guid")
    return guid


def _get_another_page(query_text, session_token=None, start_from=1, result_count=100):
    if session_token:
        stoken = session_token
    else:
        stoken = _generate_session_guid()
    query = urllib.parse.quote(query_text.lower())
    search_response = requests.get(
        url="https://www.livelib.ru/apiapp/v2.0/search/books?andyll=and7mpp4ss&fields=author_id%2C" +
            "author_name%2Cavg_mark%2Cid%2Ccount_reviews%2Cis_work%2Cname%2Cpic_200%2Cshare_url%28" +
            "share_url%29%2Cuser_book_partial%28book_read%2Crating%29&"
            f"&session_id=&count={result_count}&start={start_from}&q={query}&app_session_guid={stoken}",
        headers=REQUIRED_HEADERS
    )
    if search_response.status_code > 299:
        raise RuntimeError(f"Filed to find book in livelib by title, {search_response.text}, " +
                           f"response status: {search_response.status_code}")
    body = json.loads(search_response.text)
    if body.get('status').get('code') > 299:
        raise RuntimeError(f"Filed to find book in livelib by title, {body}, " +
                           f"response status: {body.get('status').get('code')}")
    return body


def _find_books_by_title(query_text):
    session_token = _generate_session_guid()
    first_page = _get_another_page(query_text, session_token)
    pages = math.ceil(first_page.get('count')/100)
    if pages > 1:
        results = list(first_page.get('data'))
        for i in range(1, pages):
            page = _get_another_page(query_text, session_token, start_from=i+1)
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
    if len(books) > 0:
        for book in books:
            if book.get('count_reviews') and book.get('count_reviews') > 0:
                results.append(
                    {
                        'name': str(book.get('name')),
                        'author_name': bytes(book.get('author_name'), "utf_8").decode("utf_8"),
                        'cover_image': book.get('pic_200'),
                        'url': book.get('share_url').get('share_url')
                    }
                )
    return results
