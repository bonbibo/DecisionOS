"""Email OTP login codes (draft — customer portal).

app/channels/web.py's POST /web/auth/request-code -> POST /web/auth/
verify-code flow. Replaces the old "email+phone, no verification" trust
model: a real customer portal (with case data, and eventually payment
status) needs the person logging in to actually control the email address
on file, not just be able to type it.

Codes are 6 digits, single-use, 10-minute TTL, and capped at
MAX_ATTEMPTS wrong guesses (a determined attacker with unlimited attempts
could otherwise brute-force a 6-digit space) — the cap invalidates the
code rather than locking the account, so a genuine user just requests a
fresh one.

Same "mutate in place, caller persists" contract as app.engine.
record_offer/record_message: neither function here takes a `db` or
commits.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.models import LoginCode, User

CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def create_login_code(user: User) -> str:
    """Attaches a fresh LoginCode to `user` (via the collection, so it
    cascades reliably once the caller persists `user`) and returns the
    plaintext code to send by email — the code is never stored in
    plaintext, only its hash."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    login_code = LoginCode(
        code_hash=_hash_code(code),
        expires_at=datetime.now(timezone.utc) + CODE_TTL,
        attempts=0,
    )
    user.login_codes.append(login_code)
    return code


def verify_login_code(user: User, code: str) -> bool:
    """True iff `code` matches `user`'s most recently issued LoginCode and
    that code is still unused, unexpired, and under the attempt cap.
    Marks the code used on success; increments its attempt count on a
    wrong guess. Caller persists either way."""
    # Not `max(..., key=lambda c: c.created_at)`: created_at is a server-side
    # default (func.now()), unset in Python memory until a flush happens, so
    # unflushed codes would compare None > None. Append-order is reliable
    # without needing a flush first.
    login_code = user.login_codes[-1] if user.login_codes else None
    if login_code is None:
        return False
    if login_code.used_at is not None:
        return False
    if login_code.attempts >= MAX_ATTEMPTS:
        return False
    if login_code.expires_at < datetime.now(timezone.utc):
        return False
    if login_code.code_hash != _hash_code(code):
        login_code.attempts += 1
        return False
    login_code.used_at = datetime.now(timezone.utc)
    return True
