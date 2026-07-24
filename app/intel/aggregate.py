"""Aggregate adapter listings into vault/09-Piyasa-Verisi/<dikey>.md.

Same "script generates, vault stores" pattern as app.metrics.write_dashboard
— this is the one other exception (alongside 05-Metrikler/dashboard.md) to
"the system never writes to the vault". Run via scripts/run_intel.py, daily
via cron (see docs/MASTER-SPEC-v3.md Package F).
"""

import asyncio
from datetime import date
from pathlib import Path

from app.intel import Adapter, Listing
from app.intel.bayut import BayutAdapter
from app.intel.property_finder import PropertyFinderAdapter
from app.vault import VaultReader


def _active_verticals(vault_dir: Path | str) -> list[str]:
    """Every distinct `dikey` with a `durum: aktif` vault/07-Fiyatlama/*.md note."""
    context = VaultReader(vault_dir).read_folder("07-Fiyatlama", recursive=False)
    verticals = {
        (doc.frontmatter or {}).get("dikey")
        for doc in context.documents
        if (doc.frontmatter or {}).get("durum") == "aktif" and (doc.frontmatter or {}).get("dikey")
    }
    return sorted(verticals)


async def _collect_listings(adapters: list[Adapter], dikey: str) -> list[Listing]:
    results = await asyncio.gather(*(adapter.fetch_listings(dikey) for adapter in adapters))
    return [listing for batch in results for listing in batch]


def _aggregate(listings: list[Listing]) -> dict | None:
    """None if there's nothing to report — caller must not overwrite a good
    prior note with an empty one just because this run found no listings."""
    if not listings:
        return None
    prices = [listing.price for listing in listings]
    return {
        "ortalama_kira": round(sum(prices) / len(prices)),
        "min_kira": round(min(prices)),
        "max_kira": round(max(prices)),
        "para_birimi": listings[0].currency,
        "ilan_sayisi": len(listings),
    }


def render_intel_note(dikey: str, stats: dict, kaynaklar: list[str], toplanma_tarihi: date) -> str:
    kaynaklar_yaml = "[" + ", ".join(kaynaklar) + "]"
    frontmatter = "\n".join(
        [
            "---",
            f"intel_id: PV-{dikey}",
            f"dikey: {dikey}",
            f"ortalama_kira: {stats['ortalama_kira']}",
            f"min_kira: {stats['min_kira']}",
            f"max_kira: {stats['max_kira']}",
            f"para_birimi: {stats['para_birimi']}",
            f"ilan_sayisi: {stats['ilan_sayisi']}",
            f"kaynaklar: {kaynaklar_yaml}",
            f"toplanma_tarihi: {toplanma_tarihi.isoformat()}",
            "durum: aktif",
            "---",
        ]
    )
    return f"{frontmatter}\nOtomatik toplanmış piyasa özeti — elle düzenlenmez.\n"


def write_intel_note(
    vault_dir: Path | str, dikey: str, stats: dict, kaynaklar: list[str], toplanma_tarihi: date | None = None
) -> Path:
    output_path = Path(vault_dir) / "09-Piyasa-Verisi" / f"{dikey}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_intel_note(dikey, stats, kaynaklar, toplanma_tarihi or date.today()), encoding="utf-8"
    )
    return output_path


async def run_intel_async(vault_dir: Path | str = "vault", adapters: list[Adapter] | None = None) -> list[Path]:
    """Refresh every active vertical's market intel note. Returns the paths
    actually written (a vertical with no listings this run is skipped, not
    zeroed out — see _aggregate)."""
    adapters = adapters if adapters is not None else [PropertyFinderAdapter(), BayutAdapter()]
    written: list[Path] = []
    for dikey in _active_verticals(vault_dir):
        listings = await _collect_listings(adapters, dikey)
        stats = _aggregate(listings)
        if stats is None:
            continue
        written.append(write_intel_note(vault_dir, dikey, stats, [adapter.name for adapter in adapters]))
    return written


def run_intel(vault_dir: Path | str = "vault", adapters: list[Adapter] | None = None) -> list[Path]:
    return asyncio.run(run_intel_async(vault_dir, adapters))
