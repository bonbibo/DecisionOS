"""Deep healthcheck (draft — Package J): DB, vault manifest, Stripe config.

Split into small, independently-testable check functions rather than one
inline endpoint body — each can be exercised with a broken input (bad db,
missing vault dir) without needing to break the real dependency.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.vault import VaultReader


def check_database(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # noqa: BLE001 — deliberately broad, this is a healthcheck
        return f"error: {exc}"


def check_vault_manifest(vault_dir: str = "vault") -> str:
    try:
        roles = VaultReader(vault_dir).manifest_roles()
        return "ok" if roles else "error: manifest empty or unreadable"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def check_stripe_configured() -> str:
    return "configured" if get_settings().stripe_secret_key != "change-me" else "not_configured"


def run_health_checks(db: Session, vault_dir: str = "vault") -> dict:
    checks = {
        "database": check_database(db),
        "vault_manifest": check_vault_manifest(vault_dir),
        "stripe": check_stripe_configured(),
    }
    critical_ok = checks["database"] == "ok" and checks["vault_manifest"] == "ok"
    return {"status": "ok" if critical_ok else "degraded", "checks": checks}
