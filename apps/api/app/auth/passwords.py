"""Password hashing with Argon2id.

Uses argon2-cffi with RFC 9106 recommended defaults.
Never use bcrypt, MD5, SHA, or plaintext for password storage.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Argon2id with library defaults (RFC 9106 profile)
# time_cost=3, memory_cost=65536 (64MB), parallelism=4
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id.

    Returns an encoded hash string containing the algorithm,
    parameters, salt, and hash — safe to store in the database.
    """
    return _hasher.hash(password)


def verify_password(password: str, hash: str) -> bool:
    """Verify a plaintext password against an Argon2id hash.

    Returns True if the password matches, False otherwise.
    Uses constant-time comparison internally.
    """
    try:
        return _hasher.verify(hash, password)
    except VerifyMismatchError:
        return False


def needs_rehash(hash: str) -> bool:
    """Check if a hash needs to be rehashed due to parameter changes.

    Call this after successful verification to upgrade hashes
    when Argon2 parameters are tuned.
    """
    return _hasher.check_needs_rehash(hash)
