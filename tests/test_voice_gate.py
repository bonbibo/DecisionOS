import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.engine import load_tactics
from app.models import Case, ChannelEnum, EscalationCategoryEnum, StateEnum
from app.orchestrator import _categorize_escalation, run_turn
from app.reports import compute_daily_report, render_daily_report
from app.subagents import SubagentRole, load_subagent_prompt
from app.vault import VaultReader

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"

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


class ScriptedClient:
    def __init__(self, responses):
        self._responses = {role: list(v) for role, v in responses.items()}
        self.calls = []

    def complete(self, role, system_prompt, payload):
        self.calls.append(role)
        queue = self._responses.get(role, [])
        assert queue, f"unexpected extra call to {role.value}"
        return queue.pop(0)


def _yazici():
    return json.dumps({"message": "hello", "tactic_used": "TK-001"})


def _kritik(verdict, **extra):
    return json.dumps({"verdict": verdict, **extra})


# --- _categorize_escalation ---


def test_categorize_escalation_maps_each_checklist_item():
    cases = {
        "1: floor altı teklif": EscalationCategoryEnum.floor_violation,
        "2: bilgi sızıntısı": EscalationCategoryEnum.info_leak,
        "3: uydurma bilgi": EscalationCategoryEnum.fabrication,
        "4: karşılıksız taviz": EscalationCategoryEnum.unconditional_concession,
        "5: taktik uyumsuz": EscalationCategoryEnum.tactic_mismatch,
        "6: erken kabul": EscalationCategoryEnum.premature_acceptance,
        "8: karar çelişkisi": EscalationCategoryEnum.decision_conflict,
    }
    for reason, expected in cases.items():
        assert _categorize_escalation(reason) is expected


def test_categorize_escalation_item_7_phone_request():
    assert _categorize_escalation("7: telefon istedi") is EscalationCategoryEnum.phone_request
    assert _categorize_escalation("7: Telefon numarası talep ediyor") is EscalationCategoryEnum.phone_request


def test_categorize_escalation_item_7_other_signal():
    assert _categorize_escalation("7: hukuki konu açtı") is EscalationCategoryEnum.escalation_signal_other
    assert _categorize_escalation("7: agresif dil kullandı") is EscalationCategoryEnum.escalation_signal_other


def test_categorize_escalation_falls_back_to_other():
    assert _categorize_escalation("max revisions exceeded") is EscalationCategoryEnum.other
    assert _categorize_escalation("reject after max replans") is EscalationCategoryEnum.other
    assert _categorize_escalation(None) is EscalationCategoryEnum.other
    assert _categorize_escalation("") is EscalationCategoryEnum.other


def test_categorize_escalation_uses_first_matched_item_when_multiple():
    assert _categorize_escalation("1: floor altı; 7: telefon istedi") is EscalationCategoryEnum.floor_violation


# --- run_turn wiring ---


def test_run_turn_sets_escalation_category_on_kritik_escalate(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient(
        {
            SubagentRole.analist: [ANALIST_OK],
            SubagentRole.stratejist: [STRATEJIST_OK],
            SubagentRole.yazici: [_yazici()],
            SubagentRole.kritik: [_kritik("ESCALATE", violations=["7: telefon istedi"])],
        }
    )

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert new_case.escalation_category is EscalationCategoryEnum.phone_request


def test_run_turn_sets_escalation_category_other_on_parse_failure(new_case):
    new_case.vertical = "kira-bae"
    tactics = load_tactics(VAULT_DIR)
    client = ScriptedClient({SubagentRole.analist: ["not json", "still not json"]})

    run_turn(new_case, client, "merhaba", thread=[], tactics=tactics)

    assert new_case.escalation_category is EscalationCategoryEnum.other


# --- IDENTITY_NAME templating ---


def test_load_subagent_prompt_injects_identity_name():
    text = load_subagent_prompt(SubagentRole.yazici)
    assert "{{IDENTITY_NAME}}" not in text
    assert "X Danışmanlık" in text  # default Settings.identity_name


def test_load_subagent_prompt_intake_also_injects_identity_name():
    text = load_subagent_prompt(SubagentRole.intake)
    assert "{{IDENTITY_NAME}}" not in text


# --- KR-003 / KR-004 vault content ---


def test_kr003_and_kr004_exist_as_draft_decisions():
    context = VaultReader(VAULT_DIR).read_folder("06-Kararlar", recursive=False)
    by_path = {d.path: d for d in context.documents}

    kr003 = by_path["06-Kararlar/KR-003-ses-kanali-esigi.md"]
    assert kr003.frontmatter["karar_id"] == "KR-003"
    assert kr003.frontmatter["durum"] == "taslak"

    kr004 = by_path["06-Kararlar/KR-004-sirket-kimligi.md"]
    assert kr004.frontmatter["karar_id"] == "KR-004"
    assert kr004.frontmatter["durum"] == "taslak"


def test_kr003_excluded_from_active_decision_context_while_draft():
    context = VaultReader(VAULT_DIR).read_for_role("stratejist").exclude_inactive_decisions()
    paths = {d.path for d in context.documents}
    assert "06-Kararlar/KR-003-ses-kanali-esigi.md" not in paths
    assert "06-Kararlar/KR-004-sirket-kimligi.md" not in paths


# --- app/reports.py phone_request breakdown ---


def _make_case(db_session, **overrides):
    defaults = dict(channel=ChannelEnum.whatsapp, counterparty_contact="+15550001111", state=StateEnum.discovery)
    defaults.update(overrides)
    case = Case(**defaults)
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def test_daily_report_counts_phone_request_escalations(db_session):
    target_day = date(2026, 7, 22)
    start = datetime.combine(target_day, datetime.min.time(), tzinfo=timezone.utc)

    phone = _make_case(db_session, escalation_category=EscalationCategoryEnum.phone_request)
    other = _make_case(db_session, escalation_category=EscalationCategoryEnum.floor_violation)
    for c in (phone, other):
        db_session.execute(
            Case.__table__.update().where(Case.id == c.id).values(updated_at=start + timedelta(hours=1))
        )
    db_session.commit()

    report = compute_daily_report(db_session, day=target_day)

    assert report.phone_request_escalations == 1


def test_render_daily_report_shows_phone_request_ratio(db_session):
    report = compute_daily_report(db_session, day=date(2026, 1, 1))
    text = render_daily_report(report)
    assert "Telefon talebi eskalasyonu" in text
