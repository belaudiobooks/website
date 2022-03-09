"""Utilities for downloading and resizing images (book covers, photos)."""

import io
import os
import tempfile
from PIL import Image
import requests

MAX_IMAGE_SIZE_PX = 500


def download_and_resize_image(url: str, name: str) -> str:
    """Downloads image, resizes it to match max size limit and stores in in temp folder returning path."""

    resp = requests.get(url)
    if resp.status_code != 200:
        raise ValueError(f"URL {url} returned {resp.status_code}")
    image = Image.open(io.BytesIO(resp.content))
    if not image.format:
        raise ValueError(f"Can't determine image format of URL {url}")
    img_format = image.format
    scale = MAX_IMAGE_SIZE_PX / max(image.width, image.height)
    if scale < 1:
        new_width = round(image.width * scale)
        new_height = round(image.height * scale)
        image = image.resize((new_width, new_height))

    image_page = os.path.join(tempfile.gettempdir(),
                              f'{name}.{img_format.lower()}')
    image.save(image_page)
    return image_page
