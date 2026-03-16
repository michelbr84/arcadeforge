"""Tests for Argon2id password hashing."""

from app.auth.passwords import hash_password, needs_rehash, verify_password


def test_hash_produces_argon2id():
    """Hash must use Argon2id algorithm."""
    h = hash_password("mypassword123")
    assert h.startswith("$argon2id$"), f"Expected argon2id, got: {h[:20]}"


def test_hash_is_unique_per_call():
    """Each hash must be unique due to random salt."""
    h1 = hash_password("samepassword")
    h2 = hash_password("samepassword")
    assert h1 != h2, "Hashes should differ (different salts)"


def test_verify_correct_password():
    """Correct password must verify."""
    h = hash_password("correctpassword")
    assert verify_password("correctpassword", h) is True


def test_verify_wrong_password():
    """Wrong password must not verify."""
    h = hash_password("correctpassword")
    assert verify_password("wrongpassword", h) is False


def test_verify_empty_password():
    """Empty password must not verify against a real hash."""
    h = hash_password("realpassword")
    assert verify_password("", h) is False


def test_needs_rehash_returns_bool():
    """needs_rehash should return a boolean."""
    h = hash_password("testpass")
    result = needs_rehash(h)
    assert isinstance(result, bool)
