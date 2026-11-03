"""
VedaConnect Core Security — Argon2id password hashing & JWT tokens.

Backward compatible: existing PBKDF2 passwords continue to verify.
New registrations use argon2id exclusively.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import SessionLocal
from app.models.user import UserModel
from app.models.refresh_token import RefreshTokenModel

# ── Argon2id Hasher (RFC 9106 recommended params) ───────────────
_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,       # 64 MiB
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,            # argon2id
)

# ── HTTP Bearer security scheme ─────────────────────────────────
security_scheme = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════════
#  PASSWORD HASHING
# ═══════════════════════════════════════════════════════════════

def hash_password_argon2(password: str) -> str:
    """Hash a password with argon2id. Returns the PHC-format hash string."""
    return _ph.hash(password)


def verify_password_argon2(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an argon2id hash."""
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _verify_password_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    """Legacy PBKDF2 verification for backward compatibility with existing users."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt, expected_key = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        ).hex()
        return secrets.compare_digest(key, expected_key)
    except Exception:
        return False


def verify_password_universal(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against either argon2id or legacy PBKDF2 format.
    Argon2 hashes start with '$argon2'; PBKDF2 uses 'salt$key' format.
    """
    if not hashed_password:
        return False
    if hashed_password.startswith("$argon2"):
        return verify_password_argon2(plain_password, hashed_password)
    return _verify_password_pbkdf2(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """Check if a password hash should be upgraded to argon2id."""
    if not hashed_password:
        return True
    if not hashed_password.startswith("$argon2"):
        return True  # Legacy PBKDF2 → needs rehash
    try:
        return _ph.check_needs_rehash(hashed_password)
    except Exception:
        return True


# ═══════════════════════════════════════════════════════════════
#  JWT ACCESS TOKENS
# ═══════════════════════════════════════════════════════════════

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT access token (default 15 min)."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access",
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") not in ("access", None):
            # Reject refresh tokens used as access tokens
            return None
        return payload
    except jwt.PyJWTError:
        return None


# ═══════════════════════════════════════════════════════════════
#  JWT REFRESH TOKENS
# ═══════════════════════════════════════════════════════════════

def create_refresh_token(
    user_id: str,
    family_id: Optional[str] = None,
) -> tuple[str, str, str]:
    """
    Generate a signed JWT refresh token (default 7 days).

    Returns:
        (raw_token, token_hash, family_id)
    """
    if not family_id:
        family_id = uuid.uuid4().hex

    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    jti = uuid.uuid4().hex  # unique token ID
    payload = {
        "sub": user_id,
        "jti": jti,
        "family_id": family_id,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }
    raw_token = jwt.encode(
        payload,
        settings.JWT_REFRESH_SECRET,
        algorithm=settings.ALGORITHM,
    )
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash, family_id


def decode_refresh_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT refresh token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def hash_token(raw_token: str) -> str:
    """SHA-256 hash of a raw token for storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def verify_refresh_token_family(
    raw_token: str,
    db: Session,
) -> tuple[str, str]:
    """
    Validate refresh token with reuse detection (rules.md B3).
    If a revoked token is used, revokes the entire token family.
    Returns: (new_access_token, new_refresh_token)
    """
    payload = decode_refresh_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    family_id = payload.get("family_id")
    token_h = hash_token(raw_token)

    stored = db.query(RefreshTokenModel).filter(
        RefreshTokenModel.token_hash == token_h
    ).first()

    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not recognized",
        )

    # ── Token Reuse Detection ─────────────────────────────────
    if stored.revoked:
        # Breach detected! Revoke all tokens in this family
        db.query(RefreshTokenModel).filter(
            RefreshTokenModel.family_id == family_id
        ).update({"revoked": True})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token reuse detected. All sessions in this family have been revoked.",
        )

    # Invalidate current token (rotation)
    stored.revoked = True

    # Check user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Issue new access token + new refresh token in same family
    new_access = create_access_token({"sub": user.id, "role": user.role, "email": user.email})
    new_refresh_raw, new_refresh_hash, _ = create_refresh_token(user.id, family_id=family_id)

    new_token_record = RefreshTokenModel(
        user_id=user.id,
        token_hash=new_refresh_hash,
        family_id=family_id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(new_token_record)
    db.commit()

    return new_access, new_refresh_raw


def revoke_family(family_id: str, db: Session):
    """Revoke all refresh tokens belonging to a session family on logout."""
    db.query(RefreshTokenModel).filter(
        RefreshTokenModel.family_id == family_id
    ).update({"revoked": True})
    db.commit()


# ═══════════════════════════════════════════════════════════════
#  FASTAPI DEPENDENCIES (backward compatible)
# ═══════════════════════════════════════════════════════════════

def get_db():
    """Database session dependency (mirrors existing app.auth.get_db)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """Extract current user if valid Bearer token provided, otherwise return None."""
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    user = db.query(UserModel).filter(UserModel.id == payload["sub"]).first()
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    """Require valid authenticated user from Bearer token."""
    user = get_current_user_optional(credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
