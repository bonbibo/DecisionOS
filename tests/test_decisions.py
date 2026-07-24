import json
from pathlib import Path

from app.engine import load_tactics
from app.orchestrator import run_turn
from app.subagents import SubagentRole
from app.vault import VaultReader

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


def _decision(karar_id: str, durum: str) -> str:
    return f"---\nkarar_id: {karar_id}\ndurum: {durum}\n---\n# {karar_id}\nbody\n"


def _mixed_decisions_vault(tmp_path: Path) -> Path:
    (tmp_path / "_manifest.md").write_text(
        '---\nroles:\n  stratejist: ["01-Playbooks", "06-Kararlar"]\n---\n', encoding="utf-8"
    )
    (tmp_path / "01-Playbooks").mkdir()
    (tmp_path / "01-Playbooks" / "kira-bae.md").write_text(
        "---\nplaybook_id: PB-x\n---\nplaybook body", encoding="utf-8"
    )
    kararlar = tmp_path / "06-Kararlar"
    kararlar.mkdir()
    (kararlar / "KR-001.md").write_text(_decision("KR-001", "aktif"), encoding="utf-8")
    (kararlar / "KR-002.md").write_text(_decision("KR-002", "taslak"), encoding="utf-8")
    (kararlar / "KR-003.md").write_text(_decision("KR-003", "iptal"), encoding="utf-8")
    (kararlar / "KR-004.md").write_text(_decision("KR-004", "gozden-gecirilecek"), encoding="utf-8")
    return tmp_path


def test_exclude_inactive_decisions_keeps_only_aktif(tmp_path):
    vault_dir = _mixed_decisions_vault(tmp_path)
    ctx = VaultReader(vault_dir).read_for_role("stratejist").exclude_inactive_decisions()

    decision_ids = {
        d.frontmatter["karar_id"] for d in ctx.documents if d.path.startswith("06-Kararlar/")
    }
    assert decision_ids == {"KR-001"}


def test_exclude_inactive_decisions_leaves_other_paths_untouched(tmp_path):
    vault_dir = _mixed_decisions_vault(tmp_path)
    ctx = VaultReader(vault_dir).read_for_role("stratejist").exclude_inactive_decisions()

    non_decision_paths = {d.path for d in ctx.documents if not d.path.startswith("06-Kararlar/")}
    assert non_decision_paths == {"01-Playbooks/kira-bae.md"}


def test_run_turn_stratejist_context_includes_active_decision_excludes_draft(tmp_path, new_case):
    vault_dir = _mixed_decisions_vault(tmp_path)
    new_case.vertical = "kira-bae"
    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=[], vault_dir=str(vault_dir))

    vault_payload = client.payloads[SubagentRole.stratejist][0]["VAULT"]
    decision_ids = {
        d["frontmatter"]["karar_id"] for d in vault_payload["documents"] if d["path"].startswith("06-Kararlar/")
    }
    assert decision_ids == {"KR-001"}


def test_stratejist_vault_block_includes_both_real_active_decisions(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(REAL_VAULT_DIR)
    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics, vault_dir=str(REAL_VAULT_DIR))

    vault_payload = client.payloads[SubagentRole.stratejist][0]["VAULT"]
    decision_paths = {d["path"] for d in vault_payload["documents"] if d["path"].startswith("06-Kararlar/")}
    assert decision_paths == {
        "06-Kararlar/KR-001-fiyatlama-modeli.md",
        "06-Kararlar/KR-002-dikey-sirasi.md",
    }


def test_kritik_vault_block_includes_both_real_active_decisions(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(REAL_VAULT_DIR)
    client = RecordingClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [json.dumps({"message": "hi", "tactic_used": None})],
            SubagentRole.kritik: [json.dumps({"verdict": "APPROVE"})],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics, vault_dir=str(REAL_VAULT_DIR))

    vault_payload = client.payloads[SubagentRole.kritik][0]["VAULT"]
    decision_paths = {d["path"] for d in vault_payload["documents"] if d["path"].startswith("06-Kararlar/")}
    assert decision_paths == {
        "06-Kararlar/KR-001-fiyatlama-modeli.md",
        "06-Kararlar/KR-002-dikey-sirasi.md",
    }
