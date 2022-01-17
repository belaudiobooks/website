"""
Sync books from Mininfarm which released a bunch of audiobooks on Google Disk.
We use data prepared by lit.letapis.by to get nicer list with links, titles, authors.

lit.letapis.by is down so use webarhive version
http://web.archive.org/web/20211114030539/https://lit.letapis.by/

Mininform article: http://mininform.gov.by/activities/audioknigi-izdatelstva-vysheyshaya-shkola/
Google disk (2 folders):
https://drive.google.com/drive/folders/1iqO27Mhx41slRtokWbi3J6RvTs6OArAc
https://drive.google.com/drive/folders/16K_KE8DAcBiuBjQSlsM29ypw-X5Fbq5F

To sync, first get data from lit.letapis.by by running the following script in console and save
it as mininform.json and then run this script.

console.log(JSON.stringify(Array.from(document.querySelectorAll('.book')).map(el => ({
  title: el.querySelector('.book__title').innerText.replace(/[\n\u00A0\u00AD]/g, ' '),
  author: el.querySelector('.book__sup').innerText,
  type: el.querySelector('.book__sub').innerText,
  url: el.href,
})).filter(book => book.type.toLowerCase() === 'мінінфарм'), null, 2))

"""

import json
import os
from data import books

MININFORM_JSON = os.path.join(os.path.dirname(__file__), "mininform.json")


def main() -> None:
    """Run mains"""

    data = books.read_books_data()
    assert os.path.exists(
        MININFORM_JSON), 'Follow instructions in module docstring.'
    with open(MININFORM_JSON, 'r', encoding='utf8') as f:
        mininform = json.load(f)
    for book in mininform:
        books.add_or_sync_book(data,
                               title=book["title"],
                               authors=[book["author"].title()],
                               cover_url="",
                               description="",
                               links=[books.Link("mininform", book["url"])],
                               narrators=[],
                               translators=[])
    books.write_books_data(data)


if __name__ == '__main__':
    main()
