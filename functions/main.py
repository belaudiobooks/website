import io
import os
import tempfile
import time
import functions_framework
import environ
import logging

from google.cloud import secretmanager, storage
import requests
from wand.image import Image

# Number of images to process in one run. This can be set as
# runtime variable from Google Cloud Console without the need to
# update code.
NUMBER_OF_IMAGES_TO_PROCESS = int(
    os.environ.get('NUMBER_OF_IMAGES_TO_PROCESS', '10000'))

# If set to true, the function will not upload resized images to the bucket.
# Useful to test logic without actually doing any modifications.
DRY_RUN = os.environ.get('DRY_RUN', 'false').lower() == 'true'

# List of folders with images to process. Should be in sync with books/image_cache.py
# Currently only covers are displayed in scaled-down 150x150 versions.
FOLDERS_TO_PROCESS = set(['covers'])

# List of various sizes to generate.
SIZES_TO_GENERATE = [150, 300]

# Metadata field stored on the resized image. It contains CRC32C checksum of the original
# image. This is used to ensure that the original image wasn't changed. If it was -
# the resized image is re-generated.
ORIGINAL_IMAGE_CRC32C = 'original_image_crc32c'

logging.basicConfig(
    format=
    '%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)


def get_storage_bucket(project_id: str) -> str:
    """Gets the name of the bucket where website images are stored."""
    client = secretmanager.SecretManagerServiceClient()
    settings_name = os.environ.get("SETTINGS_NAME", "django_settings")
    name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
    payload = client.access_secret_version(
        name=name).payload.data.decode("UTF-8")
    env = environ.Env()
    env.read_env(io.StringIO(payload))
    return env('GS_BUCKET_NAME')


def is_original_image(name: str) -> bool:
    """Checks whether the provided name is original, not resized image."""
    parts = os.path.split(name)
    if len(parts) != 2:
        return False
    if parts[0] not in FOLDERS_TO_PROCESS:
        return False
    if parts[1].count('.') != 1:
        return False
    return True


def generate_resized_image_name(original_file: str, size: int) -> str:
    assert original_file.count(
        '.') == 1, f'Invalid name: {original_file}. Has more than one dot.'
    parts = original_file.split('.')
    return f'{parts[0]}.s{size}.{parts[1]}'


def resize_image(name: str, blobs: dict[str,
                                        storage.Blob], bucket: storage.Bucket,
                 temp_file: str, used_images: set[str]):
    temp_resized_file = temp_file + '.resized'
    downloaded = False
    original_image = blobs[name]
    for size in SIZES_TO_GENERATE:
        resized_name = generate_resized_image_name(name, size)
        used_images.add(resized_name)
        # Check if the resized image already exists and its has CRC32C matching
        # the original image.
        if resized_name in blobs and blobs[
                resized_name].metadata is not None and blobs[
                    resized_name].metadata[
                        ORIGINAL_IMAGE_CRC32C] == original_image.crc32c:
            logging.info(f'  {resized_name} already exists')
            continue

        logging.info(f'  Resizing to {resized_name}')
        if not downloaded:
            original_image.download_to_filename(temp_file)
            downloaded = True

        with Image(filename=temp_file) as image:
            logging.info(f'  Detected format {image.format}')
            image.resize(size, size)
            image.save(filename=temp_resized_file)
        logging.info(f'  Image was resized to {size}')

        if DRY_RUN:
            logging.info('  DRY_RUN: not uploading')
        else:
            resized_blob = bucket.blob(resized_name)
            resized_blob.upload_from_filename(temp_resized_file)
            resized_blob.metadata = {
                ORIGINAL_IMAGE_CRC32C: original_image.crc32c
            }
            resized_blob.content_type = original_image.content_type
            resized_blob.update()
            time.sleep(0.5)
            logging.info('  Uploaded')


def delete_unused_resized_images(blobs: dict[str, storage.Blob],
                                 used_images: set[str]):
    logging.info('Deleting unused images')
    for ind, blob in enumerate(blobs.values()):
        name = blob.name
        # Skip images without ORIGINAL_IMAGE_CRC32C because they
        # are not resized images.
        if blob.metadata is None or blob.metadata[
                ORIGINAL_IMAGE_CRC32C] is None or name in used_images:
            continue
        if DRY_RUN:
            logging.info(f'{ind}/{len(blobs)} DRY_RUN: not deleting {name}')
        else:
            logging.info(f'{ind}/{len(blobs)} Deleting {name}')
            blob.delete()
            time.sleep(0.5)


@functions_framework.http
def resize_images(request):
    """Resizes images in the storage bucket.

    This function is triggered upon changes in the storage bucket. It goes through
    all images in the bucket and resizes  them to the sizes specified in
    SIZES_TO_GENERATE list. It skips images that already have correct resized versions
    (based on stored crc32c checksum).
    """
    logging.info('Running resize_images function')
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "audiobooksbysite")
    bucket = storage.Client().bucket(get_storage_bucket(project_id))
    blobs: dict[str, storage.Blob] = {}
    blob: storage.Blob
    for blob in bucket.list_blobs(
            fields=f'items(name,crc32c,metadata/{ORIGINAL_IMAGE_CRC32C})',
            match_glob='{' + ','.join(FOLDERS_TO_PROCESS) + '}/*'):
        blobs[blob.name] = blob

    _, temp_file = tempfile.mkstemp()

    images_left = NUMBER_OF_IMAGES_TO_PROCESS
    used_images = set()
    original_images = [
        name for name in blobs.keys() if is_original_image(name)
    ]
    for ind, name in enumerate(original_images):
        logging.info(f'{ind}/{len(original_images)} Resizing {name}')
        resize_image(name, blobs, bucket, temp_file, used_images)
        images_left -= 1
        if images_left == 0:
            break

    delete_unused_resized_images(blobs, used_images)

    website_url = os.environ.get("WEBSITE_URL")
    if website_url is not None:
        logging.info(f'Pinging {website_url}')
        requests.get(f'{website_url}/job/sync_image_cache')

    logging.info('Finished resizing images')
    return "ok"