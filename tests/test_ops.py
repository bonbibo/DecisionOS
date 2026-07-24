import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.health import check_database, check_stripe_configured, check_vault_manifest, run_health_checks
from app.models import (
    Case,
    ChannelEnum,
    LLMCall,
    OutcomeEnum,
    Payment,
    PaymentStatusEnum,
    StateEnum,
    WaitlistSignup,
)
from app.reports import compute_daily_report, render_daily_report

APP_DIR = Path(__file__).resolve().parent.parent / "app"
SECRET_SETTINGS = [
    "review_token",
    "stripe_secret_key",
    "stripe_webhook_secret",
    "whatsapp_app_secret",
    "whatsapp_access_token",
    "anthropic_api_key",
    "gmail_client_secret",
    "gmail_refresh_token",
]
LOG_CALL_RE = re.compile(r"log(?:ger)?\.(?:debug|info|warning|error|critical|exception)\(([^)]*)\)", re.DOTALL)


# --- app/health.py ---


def test_check_database_ok(db_session):
    assert check_database(db_session) == "ok"


def test_check_database_error_on_broken_session():
    class BrokenSession:
        def execute(self, *a, **k):
            raise RuntimeError("connection refused")

    result = check_database(BrokenSession())
    assert result.startswith("error:")
    assert "connection refused" in result


def test_check_vault_manifest_ok():
    assert check_vault_manifest("vault") == "ok"


def test_check_vault_manifest_error_when_missing(tmp_path):
    result = check_vault_manifest(str(tmp_path))
    assert result.startswith("error:")


def test_check_stripe_configured_reports_not_configured_by_default():
    # test settings never set a real STRIPE_SECRET_KEY
    assert check_stripe_configured() == "not_configured"


def test_run_health_checks_ok_status(db_session):
    result = run_health_checks(db_session, vault_dir="vault")
    assert result["status"] == "ok"
    assert result["checks"]["database"] == "ok"
    assert result["checks"]["vault_manifest"] == "ok"


def test_run_health_checks_degraded_when_vault_missing(db_session, tmp_path):
    result = run_health_checks(db_session, vault_dir=str(tmp_path))
    assert result["status"] == "degraded"


def test_health_deep_endpoint(api_client):
    resp = api_client.get("/health/deep")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"


def test_response_carries_request_id_header(api_client):
    resp = api_client.get("/health")
    assert "x-request-id" in {k.lower() for k in resp.headers.keys()}


# --- app/reports.py ---


def _make_case(db_session, **overrides):
    defaults = dict(channel=ChannelEnum.whatsapp, counterparty_contact="+15550001111", state=StateEnum.discovery)
    defaults.update(overrides)
    case = Case(**defaults)
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


def test_compute_daily_report_counts_within_window(db_session):
    target_day = date(2026, 7, 20)
    start = datetime.combine(target_day, datetime.min.time(), tzinfo=timezone.utc)

    won = _make_case(db_session, outcome=OutcomeEnum.won, state=StateEnum.close)
    won.closed_at = start + timedelta(hours=2)
    walked = _make_case(db_session, outcome=OutcomeEnum.walked, state=StateEnum.close)
    walked.closed_at = start + timedelta(hours=3)
    outside = _make_case(db_session, outcome=OutcomeEnum.won, state=StateEnum.close)
    outside.closed_at = start - timedelta(days=5)
    db_session.commit()

    signup = WaitlistSignup(email="a@b.com")
    db_session.add(signup)
    db_session.commit()
    db_session.execute(
        WaitlistSignup.__table__.update().where(WaitlistSignup.id == signup.id).values(created_at=start + timedelta(hours=1))
    )
    db_session.commit()

    report = compute_daily_report(db_session, day=target_day)

    assert report.closed_won == 1
    assert report.closed_walked == 1
    assert report.new_waitlist_signups == 1


def test_compute_daily_report_llm_and_payment_aggregates(db_session):
    target_day = date(2026, 7, 21)
    start = datetime.combine(target_day, datetime.min.time(), tzinfo=timezone.utc)

    case = _make_case(db_session)
    call = LLMCall(case_id=case.id, role="analist", model="x", input_tokens=100, output_tokens=20, latency_ms=5)
    db_session.add(call)
    db_session.commit()
    db_session.execute(
        LLMCall.__table__.update().where(LLMCall.id == call.id).values(created_at=start + timedelta(hours=1))
    )

    payment = Payment(
        case_id=case.id,
        access_token="tok-report-test",
        amount=500,
        captured_amount=750,
        currency="AED",
        status=PaymentStatusEnum.captured,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.execute(
        Payment.__table__.update().where(Payment.id == payment.id).values(captured_at=start + timedelta(hours=2))
    )
    db_session.commit()

    report = compute_daily_report(db_session, day=target_day)

    assert report.llm_calls == 1
    assert report.llm_input_tokens == 100
    assert report.llm_output_tokens == 20
    assert report.captured_total == 750.0


def test_render_daily_report_contains_all_metrics(db_session):
    report = compute_daily_report(db_session, day=date(2026, 1, 1))
    text = render_daily_report(report)
    for label in ["Yeni vaka", "Kapanan (kazanıldı)", "Kapanan (vazgeçildi)", "Eskale olan vaka", "LLM çağrısı", "Tahsil edilen toplam", "Yeni waitlist kaydı"]:
        assert label in text


# --- logging hygiene ---


def test_no_log_statement_references_a_secret_setting():
    offenders = []
    for path in APP_DIR.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for match in LOG_CALL_RE.finditer(text):
            call_args = match.group(1)
            for name in SECRET_SETTINGS:
                if name in call_args:
                    offenders.append(f"{path.relative_to(APP_DIR.parent)}: ...{name}... in a log call")
    assert offenders == [], f"log statements referencing secret settings: {offenders}"
