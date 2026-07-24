from pathlib import Path

import pytest

from app.engine import (
    NegotiationEngine,
    load_playbooks,
    load_tactics,
    tactics_for_stage,
)
from app.models import StateEnum

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"


def test_load_tactics_reads_all_notes_from_the_vault():
    tactics = load_tactics(VAULT_DIR)
    ids = {t.taktik_id for t in tactics}
    assert ids == {"TK-001", "TK-002", "TK-003"}


def test_load_playbooks_reads_kira_bae():
    playbooks = load_playbooks(VAULT_DIR)
    assert len(playbooks) == 1
    assert playbooks[0].playbook_id == "PB-kira-bae"
    assert playbooks[0].dikey == "kira-bae"


def test_tactics_for_stage_filters_by_dikey_and_asama():
    tactics = load_tactics(VAULT_DIR)

    counter_tactics = tactics_for_stage(tactics, "kira-bae", StateEnum.counter)
    assert {t.taktik_id for t in counter_tactics} == {"TK-001", "TK-003"}

    concession_tactics = tactics_for_stage(tactics, "kira-bae", StateEnum.concession)
    assert {t.taktik_id for t in concession_tactics} == {"TK-002"}

    assert tactics_for_stage(tactics, "other-vertical", StateEnum.counter) == []


def test_negotiation_engine_available_tactics_follows_case_vertical_and_state(new_case):
    new_case.vertical = "kira-bae"
    engine = NegotiationEngine(new_case, tactics=load_tactics(VAULT_DIR))

    assert engine.available_tactics() == []  # discovery has no tactics yet

    engine.start_anchor()
    engine.receive_counter()
    assert {t.taktik_id for t in engine.available_tactics()} == {"TK-001", "TK-003"}

    engine.make_concession()
    assert {t.taktik_id for t in engine.available_tactics()} == {"TK-002"}


def test_negotiation_engine_available_tactics_empty_without_vertical(new_case):
    engine = NegotiationEngine(new_case, tactics=load_tactics(VAULT_DIR))
    engine.start_anchor()
    engine.receive_counter()
    assert engine.available_tactics() == []


def test_inactive_tactic_is_excluded(tmp_path):
    taktikler_dir = tmp_path / "01-Playbooks" / "taktikler"
    taktikler_dir.mkdir(parents=True)
    (taktikler_dir / "TK-999-taslak.md").write_text(
        """---
taktik_id: TK-999
ad: Taslak Taktik
dikey: test-dikey
asama: counter
durum: taslak
kullanilma_sayisi: 0
basari_sayisi: 0
basari_orani: 0.0
risk: dusuk
guncelleme: 2026-07-24
---

# Taslak Taktik
""",
        encoding="utf-8",
    )

    tactics = load_tactics(tmp_path)
    assert len(tactics) == 1
    assert tactics[0].is_active is False
    assert tactics_for_stage(tactics, "test-dikey", StateEnum.counter) == []
