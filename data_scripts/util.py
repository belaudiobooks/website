'''Shared utils used by data sync scripts.'''

import bs4
import requests


def open_url(url: str) -> bs4.BeautifulSoup:
    '''Fetches and parses html page.'''
    resp = requests.get(url)
    resp.encoding = 'utf8'
    if resp.status_code != 200:
        raise ValueError(f'URL {url} returned {resp.status_code}')
    return bs4.BeautifulSoup(resp.text, 'html.parser')
