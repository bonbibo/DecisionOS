from datetime import datetime, timedelta, timezone

from app.auth import MAX_ATTEMPTS, create_login_code, verify_login_code
from app.models import LoginCode


def test_create_login_code_returns_six_digit_plaintext(make_user):
    user = make_user()
    code = create_login_code(user)
    assert len(code) == 6
    assert code.isdigit()
    assert len(user.login_codes) == 1
    assert user.login_codes[0].code_hash != code  # never stored in plaintext


def test_verify_login_code_succeeds_with_correct_code(make_user):
    user = make_user()
    code = create_login_code(user)

    assert verify_login_code(user, code) is True
    assert user.login_codes[0].used_at is not None


def test_verify_login_code_fails_with_wrong_code(make_user):
    user = make_user()
    create_login_code(user)

    assert verify_login_code(user, "000000") is False
    assert user.login_codes[0].used_at is None
    assert user.login_codes[0].attempts == 1


def test_verify_login_code_fails_when_already_used(make_user):
    user = make_user()
    code = create_login_code(user)
    assert verify_login_code(user, code) is True

    assert verify_login_code(user, code) is False


def test_verify_login_code_fails_when_expired(make_user):
    user = make_user()
    code = create_login_code(user)
    user.login_codes[0].expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    assert verify_login_code(user, code) is False


def test_verify_login_code_fails_after_max_attempts(make_user):
    user = make_user()
    code = create_login_code(user)

    for _ in range(MAX_ATTEMPTS):
        assert verify_login_code(user, "000000") is False

    # Even the correct code no longer works once the cap is hit.
    assert verify_login_code(user, code) is False


def test_verify_login_code_false_with_no_codes_issued(make_user):
    user = make_user()
    assert verify_login_code(user, "123456") is False


def test_verify_login_code_uses_most_recent_code(make_user):
    user = make_user()
    old_code = create_login_code(user)
    new_code = create_login_code(user)

    assert old_code != new_code
    assert verify_login_code(user, old_code) is False
    assert verify_login_code(user, new_code) is True


def test_login_code_persists_via_user_relationship(db_session, make_user):
    user = make_user()
    create_login_code(user)
    db_session.commit()

    rows = db_session.query(LoginCode).filter(LoginCode.user_id == user.id).all()
    assert len(rows) == 1
