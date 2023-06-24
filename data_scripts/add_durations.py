import datetime
import os
import subprocess
from typing import List, Optional
import bs4
import requests
from . import books

MININFORM_DIRS = [
    entry for entry in os.walk('/home/nbeloglazov/audiobooks/Аудиокниги')
]


def _get_page(url: str) -> bs4.BeautifulSoup:
    resp = requests.get(url)
    resp.encoding = 'utf8'
    if resp.status_code != 200:
        raise ValueError(f'URL {url} returned {resp.status_code}')
    return bs4.BeautifulSoup(resp.text, 'html.parser')


def _get_duration_from_folder(folder_or_file: str) -> int:
    mp3_files = []
    for dirroot, _, files in os.walk(folder_or_file):
        for file in files:
            if not file.endswith('.mp3'):
                continue
            path = os.path.join(dirroot, file)
            mp3_files.append(path)
    if folder_or_file.endswith('.mp3'):
        mp3_files.append(folder_or_file)
    duration_sec = 0
    for file in mp3_files:
        print(f'reading duration of {file}')
        dur_str: str = subprocess.check_output(
            f'ffprobe -i \'{file}\' -show_entries format=duration -v quiet -of csv="p=0"',
            shell=True,
            encoding='utf8')

        duration_sec += int(float(dur_str.strip()))
    return duration_sec


def _download_files_and_get_duration(urls: List[str]) -> int:
    if len(urls) == 0:
        return 0
    tmp_dir = '/tmp/files'
    os.system(f'rm -rf {tmp_dir} && mkdir {tmp_dir}')
    lines = ' '.join([f'\'{url}\'' for url in urls])
    os.system(
        f'echo {lines} | xargs -n 1 -P 8 wget --content-disposition -P {tmp_dir}'
    )
    return _get_duration_from_folder(tmp_dir)


def _get_kamunitak_duration_sec(url: str) -> int:
    html = _get_page(url)
    mp3_links = []
    for anchor in html.select('.VolumeMedia .ChapterContainer > a[href]'):
        link = anchor['href']
        if '.mp3' in link:
            mp3_links.append(f'https://kamunikat.org/{link}')
    return _download_files_and_get_duration(mp3_links)


def _find_dir_or_file(name: str) -> Optional[str]:
    candidates = [
        entry for entry in MININFORM_DIRS
        if name in entry[2] or name in entry[1]
    ]
    if len(candidates) == 0:
        return None
    elif len(candidates) == 1:
        return os.path.join(candidates[0][0], name)
    else:
        print('found multiple candidates')
        for candidate in candidates:
            print(f'candidate: {candidate}')
            is_correct = input('correct? -> ')
            if is_correct == 'y' or is_correct == 'yes':
                return os.path.join(candidate[0], name)
    return None


def _get_mininfarm_duration_sec(url: str) -> int:
    html = _get_page(url)
    name = html.select_one('title').string.removesuffix(' - Google Drive')
    folder_or_file = _find_dir_or_file(name)
    if folder_or_file is None:
        print('Did not find folder for {name}')
        return 0
    return _get_duration_from_folder(folder_or_file)


def _get_knihi_com_duration_sec(url: str) -> int:
    html = _get_page(url)
    mp3_links = []
    for anchor in html.select('a[href]'):
        link = anchor['href']
        if link.endswith('.mp3') and link.startswith('https://'):
            mp3_links.append(link)
    return _download_files_and_get_duration(mp3_links)


def run(data: books.BooksData) -> None:
    '''See module description.'''
    for book in data.books:
        print(book.narration.first().links.first())
        for narration in book.narration.all():
            if narration.duration and narration.duration.total_seconds() != 0:
                continue
            for link in narration.links.all():
                found = False
                if not found and link.url_type.name == 'mininform':
                    print(
                        f'\n\n\nprocessing {book.title} {book.authors.first()}'
                    )
                    print(link.url)
                    found = True
                    duration = _get_mininfarm_duration_sec(link.url)
                    print(duration)
                    narration.duration = datetime.timedelta(seconds=duration)
                    print(f'Slug is {book.slug}')
                    narration.save()
