import json
from pathlib import Path

import pytest

from app.intake import _get_intel as intake_get_intel
from app.intel import Listing
from app.intel.aggregate import (
    _active_verticals,
    _aggregate,
    render_intel_note,
    run_intel,
    run_intel_async,
    write_intel_note,
)
from app.intel.bayut import BayutAdapter
from app.intel.property_finder import PropertyFinderAdapter
from app.orchestrator import _get_intel as orchestrator_get_intel
from app.orchestrator import run_turn
from app.subagents import SubagentRole

REAL_VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"

ANALIST_OK = json.dumps({"archetype": "A2", "recommended_state": "anchoring"})
STRATEJIST_OK = json.dumps(
    {
        "anchor": 90000,
        "target": 95000,
        "floor": 85000,
        "concession_ladder": [4000, 2000, 1000],
        "primary_tactics": ["TK-001"],
        "fallback_tactics": [],
    }
)


class RecordingClient:
    def __init__(self, responses: dict[SubagentRole, list[str]]):
        self._responses = {role: list(v) for role, v in responses.items()}
        self.payloads: dict[SubagentRole, list[dict]] = {}

    def complete(self, role, system_prompt, payload):
        self.payloads.setdefault(role, []).append(payload)
        return self._responses[role].pop(0)


def _pricing_vault(tmp_path: Path, verticals: list[tuple[str, str]]) -> Path:
    """verticals: [(dikey, durum), ...]"""
    (tmp_path / "_manifest.md").write_text(
        '---\nroles:\n  stratejist: ["07-Fiyatlama", "09-Piyasa-Verisi"]\n---\n', encoding="utf-8"
    )
    fiyatlama = tmp_path / "07-Fiyatlama"
    fiyatlama.mkdir()
    for dikey, durum in verticals:
        (fiyatlama / f"{dikey}.md").write_text(
            f"---\nfiyat_id: FY-{dikey}\ndikey: {dikey}\ndurum: {durum}\n---\nbody\n", encoding="utf-8"
        )
    return tmp_path


class FakeAdapter:
    def __init__(self, name: str, listings: list[Listing]):
        self.name = name
        self._listings = listings

    async def fetch_listings(self, dikey: str) -> list[Listing]:
        return list(self._listings)


# --- adapters ---


@pytest.mark.asyncio
async def test_property_finder_default_fetch_returns_empty_stub():
    adapter = PropertyFinderAdapter()
    assert await adapter.fetch_listings("kira-bae") == []


@pytest.mark.asyncio
async def test_bayut_default_fetch_returns_empty_stub():
    adapter = BayutAdapter()
    assert await adapter.fetch_listings("kira-bae") == []


@pytest.mark.asyncio
async def test_adapter_uses_injected_fetch_fn():
    async def fake_fetch(dikey):
        return [Listing(price=90000, currency="AED", bedrooms=1, url="http://x")]

    adapter = PropertyFinderAdapter(fetch_fn=fake_fetch)
    listings = await adapter.fetch_listings("kira-bae")
    assert len(listings) == 1
    assert listings[0].price == 90000


# --- aggregate helpers ---


def test_active_verticals_excludes_demo(tmp_path):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif"), ("arac-bae", "demo")])
    assert _active_verticals(vault_dir) == ["kira-bae"]


def test_aggregate_computes_stats():
    listings = [
        Listing(price=90000, currency="AED", bedrooms=1, url="a"),
        Listing(price=100000, currency="AED", bedrooms=2, url="b"),
        Listing(price=80000, currency="AED", bedrooms=1, url="c"),
    ]
    stats = _aggregate(listings)
    assert stats == {
        "ortalama_kira": 90000,
        "min_kira": 80000,
        "max_kira": 100000,
        "para_birimi": "AED",
        "ilan_sayisi": 3,
    }


def test_aggregate_returns_none_for_empty_listings():
    assert _aggregate([]) is None


def test_render_intel_note_frontmatter_shape():
    from datetime import date

    stats = {"ortalama_kira": 92500, "min_kira": 78000, "max_kira": 115000, "para_birimi": "AED", "ilan_sayisi": 34}
    text = render_intel_note("kira-bae", stats, ["property-finder", "bayut"], date(2026, 7, 25))
    assert "intel_id: PV-kira-bae" in text
    assert "dikey: kira-bae" in text
    assert "ortalama_kira: 92500" in text
    assert "kaynaklar: [property-finder, bayut]" in text
    assert "toplanma_tarihi: 2026-07-25" in text
    assert "durum: aktif" in text


def test_write_intel_note_creates_folder_and_file(tmp_path):
    stats = {"ortalama_kira": 90000, "min_kira": 80000, "max_kira": 100000, "para_birimi": "AED", "ilan_sayisi": 2}
    path = write_intel_note(tmp_path, "kira-bae", stats, ["property-finder"])
    assert path == tmp_path / "09-Piyasa-Verisi" / "kira-bae.md"
    assert path.exists()
    assert "dikey: kira-bae" in path.read_text(encoding="utf-8")


# --- run_intel / run_intel_async ---


@pytest.mark.asyncio
async def test_run_intel_async_writes_note_for_active_vertical(tmp_path):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    adapters = [
        FakeAdapter("property-finder", [Listing(90000, "AED", 1, "a")]),
        FakeAdapter("bayut", [Listing(100000, "AED", 2, "b")]),
    ]

    written = await run_intel_async(vault_dir, adapters)

    assert written == [vault_dir / "09-Piyasa-Verisi" / "kira-bae.md"]
    text = written[0].read_text(encoding="utf-8")
    assert "ilan_sayisi: 2" in text
    assert "kaynaklar: [property-finder, bayut]" in text


@pytest.mark.asyncio
async def test_run_intel_async_skips_vertical_with_no_listings(tmp_path):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    adapters = [FakeAdapter("property-finder", []), FakeAdapter("bayut", [])]

    written = await run_intel_async(vault_dir, adapters)

    assert written == []
    assert not (vault_dir / "09-Piyasa-Verisi").exists()


@pytest.mark.asyncio
async def test_run_intel_async_does_not_overwrite_existing_note_with_empty_run(tmp_path):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    write_intel_note(
        vault_dir,
        "kira-bae",
        {"ortalama_kira": 1, "min_kira": 1, "max_kira": 1, "para_birimi": "AED", "ilan_sayisi": 1},
        ["property-finder"],
    )
    before = (vault_dir / "09-Piyasa-Verisi" / "kira-bae.md").read_text(encoding="utf-8")

    await run_intel_async(vault_dir, [FakeAdapter("property-finder", [])])

    after = (vault_dir / "09-Piyasa-Verisi" / "kira-bae.md").read_text(encoding="utf-8")
    assert before == after


def test_run_intel_sync_wrapper_works(tmp_path):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    written = run_intel(vault_dir, [FakeAdapter("property-finder", [Listing(90000, "AED", 1, "a")])])
    assert written == [vault_dir / "09-Piyasa-Verisi" / "kira-bae.md"]


# --- _get_intel (orchestrator + intake) ---


def test_orchestrator_get_intel_returns_frontmatter_for_active_note(tmp_path, new_case):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    write_intel_note(
        vault_dir,
        "kira-bae",
        {"ortalama_kira": 92500, "min_kira": 78000, "max_kira": 115000, "para_birimi": "AED", "ilan_sayisi": 34},
        ["property-finder", "bayut"],
    )
    new_case.vertical = "kira-bae"

    intel = orchestrator_get_intel(new_case, str(vault_dir))

    assert intel["ortalama_kira"] == 92500
    assert intel["ilan_sayisi"] == 34


def test_orchestrator_get_intel_empty_when_no_note(tmp_path, new_case):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    new_case.vertical = "kira-bae"
    assert orchestrator_get_intel(new_case, str(vault_dir)) == {}


def test_orchestrator_get_intel_empty_without_vertical(new_case):
    new_case.vertical = None
    assert orchestrator_get_intel(new_case, "vault") == {}


def test_intake_get_intel_mirrors_orchestrator(tmp_path, new_case):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    write_intel_note(
        vault_dir,
        "kira-bae",
        {"ortalama_kira": 92500, "min_kira": 78000, "max_kira": 115000, "para_birimi": "AED", "ilan_sayisi": 34},
        ["bayut"],
    )
    new_case.vertical = "kira-bae"
    assert intake_get_intel(new_case, str(vault_dir))["ortalama_kira"] == 92500


# --- run_turn auto-populates INTEL ---


def test_run_turn_auto_populates_intel_from_vault(tmp_path, new_case):
    vault_dir = _pricing_vault(tmp_path, [("kira-bae", "aktif")])
    (tmp_path / "01-Playbooks").mkdir()
    (tmp_path / "06-Kararlar").mkdir()
    write_intel_note(
        vault_dir,
        "kira-bae",
        {"ortalama_kira": 92500, "min_kira": 78000, "max_kira": 115000, "para_birimi": "AED", "ilan_sayisi": 34},
        ["bayut"],
    )
    (tmp_path / "_manifest.md").write_text(
        '---\nroles:\n  analist: []\n  stratejist: ["01-Playbooks", "06-Kararlar", "07-Fiyatlama", "09-Piyasa-Verisi"]\n  yazici: []\n  kritik: []\n---\n',
        encoding="utf-8",
    )
    new_case.vertical = "kira-bae"
    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=[], vault_dir=str(tmp_path))

    payload = client.payloads[SubagentRole.stratejist][0]
    assert payload["INTEL"]["ortalama_kira"] == 92500


def test_run_turn_explicit_intel_overrides_vault(new_case):
    new_case.vertical = "kira-bae"
    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=[], intel={"manual": True})

    payload = client.payloads[SubagentRole.stratejist][0]
    assert payload["INTEL"] == {"manual": True}


def test_run_turn_intel_empty_when_no_vault_note(new_case):
    new_case.vertical = "kira-bae"
    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=[], vault_dir=str(REAL_VAULT_DIR))

    payload = client.payloads[SubagentRole.stratejist][0]
    assert payload["INTEL"] == {}
