"""Bayut adapter (draft — Package F).

Same status as app.intel.property_finder: real scraping target is
Crawlee/Playwright against bayut.com, but live selectors are unverified —
see docs/MASTER-SPEC-v3.md Package F, "İNSAN GEREKLİ". `_default_fetch` is
a stub; real usage/tests inject `fetch_fn` instead.
"""

import logging
from typing import Awaitable, Callable

from app.intel import Listing

logger = logging.getLogger(__name__)

FetchFn = Callable[[str], Awaitable[list[Listing]]]


class BayutAdapter:
    name = "bayut"

    def __init__(self, fetch_fn: FetchFn | None = None):
        self._fetch_fn = fetch_fn or self._default_fetch

    async def fetch_listings(self, dikey: str) -> list[Listing]:
        return await self._fetch_fn(dikey)

    async def _default_fetch(self, dikey: str) -> list[Listing]:
        logger.warning(
            "BayutAdapter._default_fetch is a stub (no live selectors yet) — "
            "returning no listings for dikey=%s",
            dikey,
        )
        return []
