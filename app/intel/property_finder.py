"""Property Finder adapter (draft — Package F).

Real scraping is Crawlee (Python package) + Playwright (already provisioned
in this environment) against propertyfinder.ae, but the live CSS/XPath
selectors were never verified against the real site — see
docs/MASTER-SPEC-v3.md Package F, "İNSAN GEREKLİ". `_default_fetch` is
therefore a stub that returns no listings rather than a guess at selectors
that would silently break; real usage/tests inject `fetch_fn` instead.
"""

import logging
from typing import Awaitable, Callable

from app.intel import Listing

logger = logging.getLogger(__name__)

FetchFn = Callable[[str], Awaitable[list[Listing]]]


class PropertyFinderAdapter:
    name = "property-finder"

    def __init__(self, fetch_fn: FetchFn | None = None):
        self._fetch_fn = fetch_fn or self._default_fetch

    async def fetch_listings(self, dikey: str) -> list[Listing]:
        return await self._fetch_fn(dikey)

    async def _default_fetch(self, dikey: str) -> list[Listing]:
        logger.warning(
            "PropertyFinderAdapter._default_fetch is a stub (no live selectors yet) — "
            "returning no listings for dikey=%s",
            dikey,
        )
        return []
