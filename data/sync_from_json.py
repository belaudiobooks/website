"""Syncer that adds book from manual_book.json file.

Use this syncer to add one-off book if needed: modify manual_book.json and run syncer.
"""

import json
import os
from . import books

MANUAL_DATA = os.path.dirname(os.path.realpath(__file__)) + "/manual_book.json"


def main():
    "Adds book from manual_book.json to data.json."
    data = books.read_books_data()
    with open(MANUAL_DATA, "r", encoding="utf8") as f:
        data_json = json.load(f)
        for author in data_json:
            for book in author["books"]:
                title = book["title"]
                print(f"processing {title}")
                books.add_or_sync_book(
                    data,
                    title=title,
                    description=book["description"],
                    authors=[author["name"]],
                    narrators=[],
                    translators=[],
                    cover_url=book["cover"],
                    links=[books.Link(**link) for link in book["links"]])
    books.write_books_data(data)


if __name__ == '__main__':
    main()
