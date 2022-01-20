from typing import Any, Dict


TAG_MAPPING = {
    "promo": _handle_promo,
    "Дзіцячыя": _handle_kids,
    "Сучасныя": _handle_modern,
    "Класічныя": _handle_classic,
    "Замежныя": _handle_foreign
}

def function_handler(request: Dict[str, Any]) -> None:
    tag = request.get("tag")
    filter_books = request.get("filter_books")
    # validate input
    _handle_tag(tag, filter_books)


def _handle_tag(tag: str, filter_books: str) -> None:
    tag_handler = TAG_MAPPING.get(tag)
    # handle tag
    tag_handler(filter_books)


def _handle_promo(filter_books: str) -> None:
    # do something related to create
    return


def _handle_kids(filter_books: str) -> None:
    # do something related to activate
    return


def _handle_modern(filter_books: str) -> None:
    # do something related to suspend
    return


def _handle_classic(filter_books: str) -> None:
    # do something related to delete
    return

def _handle_foreign(filter_books: str) -> None:
    # do something related to delete
    return