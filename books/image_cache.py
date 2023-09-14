"""
This module provides functions to control cache of resized images. The cache doesn't store the
images themselves. Instead it stores mapping from image URLs to their resized versions. The
cache is regularly updated to make sure that it's up-to-date.

For an image with path 'covers/something.png' resized images are stored as 
'covers/something.s100.png' where s100 indicates that the size of 100x100 pixels.
"""
from os import path

from django.core.cache import cache
from django.core.files.storage import default_storage
from django.conf import settings

# Process only covers for now. We don't have pages where we display
# multiple photos or publisher logos.
FOLDERS = ['covers']


def sync_cache():
    """
    Updates cache of resized images.
    """
    sizes: dict[str, dict[int, str]] = {}
    for folder in FOLDERS:
        if not default_storage.exists(folder):
            # It might happen when running `python manage.py collectstatic`.
            # In that case `media` folder doesn't exist and this function fails.
            continue
        files: list[str] = default_storage.listdir(folder)[1]
        for file_name in files:
            parts = path.basename(file_name).split('.')
            if len(parts) == 2:
                continue
            size = int(parts[1].removeprefix('s'))
            original_url = f'{settings.MEDIA_URL}{folder}/{parts[0]}.{parts[2]}'
            if original_url not in sizes:
                sizes[original_url] = {}
            sizes[original_url][
                size] = f'{settings.MEDIA_URL}{folder}/{file_name}'
    cache.set('image_cache', sizes, timeout=None)


def get_image_for_size(filename: str, size: int) -> str:
    """
    Given original image filename and desired size returns URL of the resized image,
    if it exists. If it doesn't, returns original filename.
    """
    sizes: dict[str, dict[int, str]] = cache.get('image_cache')
    if sizes is None:
        return filename
    if filename not in sizes:
        return filename
    if size not in sizes[filename]:
        return filename
    return sizes[filename][size]