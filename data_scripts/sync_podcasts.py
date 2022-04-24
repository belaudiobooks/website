'''Syncs books from podcast rss files.'''

from dataclasses import dataclass
import datetime
from typing import Dict, List, Optional
import django
import requests
import feedparser

from . import books


@dataclass
class Podcast:
    '''Config of podcast that contains necessary info sync it.'''
    rss_feed: str
    # By default podcasts links will be fetched from podcast.ru but this
    # field allows to override those links or add ones the missing in podcast.ru
    podcasts: Dict[str, str]
    # Podcasts don't have 'narrator' field in RSS so narrators need to be provided
    # explicitly.
    narrators: List[str]


# List of known podcasts containing belarusian audiobooks
PODCASTS = [
    Podcast(
        rss_feed=
        'https://storage.googleapis.com/belaudiobooks/uladzimir_sadouski_1813/rss.xml',
        podcasts={},
        narrators=['Ірына Якавец'],
    ),
]


def _find_apple_podcast_id(title: str) -> Optional[int]:
    '''Helper function to find id of an podcast on apple. This needed for podcast.ru later.'''
    params = {'media': 'podcast', 'term': title}

    resp = requests.get('https://itunes.apple.com/search',
                        params=params).json()
    if resp['resultCount'] == 0:
        return None
    return resp['results'][0]['collectionId']


def _get_podcast_urls(title: str) -> Dict[str, str]:
    '''Using API of podcast.ru get links to popular podcast platforms for given book.'''
    apple_id = _find_apple_podcast_id(title)
    if apple_id is None:
        print(
            f'Could not find apple podcast for "{title}". Not using podcast.ru to get links.'
        )
        return {}
    # podcast.ru uses graphql. This is just copy-pasted from XHR request that is sent from any
    # podcast.ru page that shows podcast. Check devtools.
    query = '{"operationName":"GetPodcast","variables":{"id":' + str(
        apple_id
    ) + '},"query":"query GetPodcast($id: Int!) { podcast(id: $id) ' + \
        '{ linkCastbox linkSpotify linkGoogle linkItunes linkYandex}}"}'
    resp = requests.post('https://podcast.ru/graphql', data=query).json()
    links = resp['data']['podcast']
    return {
        'google_podcast': links['linkGoogle'],
        'apple_podcast': links['linkItunes'],
        'yandex_podcast': links['linkYandex'],
        'spotify_podcast': links['linkSpotify'],
        'castbox_podcast': links['linkCastbox'],
    }


def _sync_from_podcast(data: books.BooksData, podcast: Podcast) -> None:
    rss = feedparser.parse(podcast.rss_feed)
    feed = rss['feed']
    title = feed['title']
    print(f'processing {title}')
    description = feed.get('summary')
    author = feed['author']
    cover_url = feed['image']['href']
    duration = datetime.timedelta()
    for episode in rss['entries']:
        duration += django.utils.dateparse.parse_duration(
            episode['itunes_duration'])

    narration = books.add_or_update_book(data,
                                         title=title,
                                         description=description,
                                         authors=[author],
                                         narrators=podcast.narrators,
                                         translators=[],
                                         cover_url=cover_url,
                                         duration_sec=int(
                                             duration.total_seconds()))

    links_dict = _get_podcast_urls(title)
    links_dict.update(podcast.podcasts)
    for link_type, url in links_dict.items():
        if url is None:
            print(f'URL for podcast {link_type} is missing')
        else:
            books.add_or_update_link(narration=narration,
                                     url_type=link_type,
                                     url=url)


def run(data: books.BooksData) -> None:
    '''Run mains'''
    for podcast in PODCASTS[0:1]:
        _sync_from_podcast(data, podcast)
