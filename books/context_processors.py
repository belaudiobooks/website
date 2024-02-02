from typing import Dict
from django.conf import settings
from django.http import HttpRequest


def algolia(request: HttpRequest) -> Dict[str, str]:
    """Adds algolia keys necessary to support client-side search."""
    return {
        "algolia_index": settings.ALGOLIA_INDEX,
        "algolia_application_id": settings.ALGOLIA_APPLICATION_ID,
        "algolia_search_key": settings.ALGOLIA_SEARCH_KEY,
    }
