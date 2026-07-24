"""Market intel adapters (draft — Package F).

Each adapter fetches comparable listings for a vault vertical (`dikey`) from
one external source (Property Finder, Bayut). Adapters never write to the
vault themselves — app.intel.aggregate does that, following the same
"script generates, vault stores" pattern as app.metrics/dashboard.md.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Listing:
    """One comparable listing, normalized across sources."""

    price: float
    currency: str
    bedrooms: int | None
    url: str


class Adapter(Protocol):
    """The seam every market-data source implements. `name` is the string
    recorded in a generated intel note's `kaynaklar` frontmatter list."""

    name: str

    async def fetch_listings(self, dikey: str) -> list[Listing]:
        """Comparable listings for `dikey` (e.g. "kira-bae"). Empty list, not
        an exception, if the source has nothing or isn't reachable."""
        ...
