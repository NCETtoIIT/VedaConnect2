"""
VedaConnect Auth v2 API — Argon2id, Dual-Token (Access 15m + Refresh 7d), Token Rotation & Reuse Detection.
Path: /api/v1/auth
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    hash_password_argon2,
    verify_password_universal,
    needs_rehash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token_family,
    revoke_family,
    decode_refresh_token,
    get_current_user,
    get_db,
)
from app.core.audit import log_audit
from app.models.user import UserModel
from app.models.refresh_token import RefreshTokenModel
from app.limiter import safe_rate_limit

router = APIRouter(prefix="/api/v1/auth", tags=["VedaConnect Authentication & Access Control (v2)"])


# ── Schemas ──────────────────────────────────────────────────────
class RegisterV2Request(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "patient"
    phone: Optional[str] = None
    hospital_id: Optional[str] = None


class LoginV2Request(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenV2Response(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


# ── Endpoints ───────────────────────────────────────────────────

@router.post("/register", response_model=TokenV2Response)
@safe_rate_limit("15/minute")
def register_v2(req: RegisterV2Request, request: Request = None, db: Session = Depends(get_db)):
    """Register a new user with Argon2id password hashing and issue dual tokens."""
    email_clean = req.email.strip().lower()

    if db.query(UserModel).filter(UserModel.email.ilike(email_clean)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    user_id = str(uuid.uuid4())
    pw_hash = hash_password_argon2(req.password)

    new_user = UserModel(
        id=user_id,
        email=email_clean,
        name=req.name.strip(),
        role=req.role.strip().lower(),
        phone=req.phone,
        hospital_id=req.hospital_id,
        password_hash=pw_hash,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue dual tokens
    access_token = create_access_token({
        "sub": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        "name": new_user.name,
        "hospital_id": new_user.hospital_id,
    })

    refresh_raw, refresh_hash, family_id = create_refresh_token(new_user.id)
    token_record = RefreshTokenModel(
        user_id=new_user.id,
        token_hash=refresh_hash,
        family_id=family_id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(token_record)
    db.commit()

    log_audit(db, new_user.id, new_user.role, "register", "users", new_user.id, "account_creation", request)

    return TokenV2Response(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role,
            "phone": new_user.phone,
            "hospital_id": new_user.hospital_id,
        }
    )


@router.post("/login", response_model=TokenV2Response)
@safe_rate_limit("30/minute")
def login_v2(req: LoginV2Request, request: Request = None, db: Session = Depends(get_db)):
    """Authenticate with Argon2id / PBKDF2 universal verification and return access + refresh tokens."""
    email_clean = req.email.strip().lower()
    user = db.query(UserModel).filter(UserModel.email.ilike(email_clean)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Password check
    if user.password_hash:
        if not verify_password_universal(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )
        # Automatic rehash upgrade to Argon2id if legacy hash
        if needs_rehash(user.password_hash):
            user.password_hash = hash_password_argon2(req.password)
            db.commit()
    else:
        # First-time seed login: set Argon2id hash
        user.password_hash = hash_password_argon2(req.password)
        db.commit()

    # Role enforcement
    if req.role:
        if user.role.lower() != req.role.strip().lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Account role is '{user.role}'."
            )

    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "hospital_id": user.hospital_id,
    })

    refresh_raw, refresh_hash, family_id = create_refresh_token(user.id)
    token_record = RefreshTokenModel(
        user_id=user.id,
        token_hash=refresh_hash,
        family_id=family_id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )
    db.add(token_record)
    db.commit()

    log_audit(db, user.id, user.role, "login", "users", user.id, "authentication", request)

    return TokenV2Response(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "phone": user.phone,
            "hospital_id": user.hospital_id,
        }
    )


@router.post("/refresh")
@safe_rate_limit("60/minute")
def refresh_token_endpoint(req: RefreshTokenRequest, request: Request = None, db: Session = Depends(get_db)):
    """Rotate refresh token and detect reuse (rules.md B3)."""
    new_access, new_refresh = verify_refresh_token_family(req.refresh_token, db)
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
def logout_endpoint(req: RefreshTokenRequest, request: Request = None, db: Session = Depends(get_db)):
    """Revoke refresh token family upon user logout."""
    payload = decode_refresh_token(req.refresh_token)
    if payload and "family_id" in payload:
        revoke_family(payload["family_id"], db)
    return {"message": "Logged out successfully. Session revoked."}


@router.get("/me")
def get_current_user_profile(user: UserModel = Depends(get_current_user)):
    """Return profile for the currently authenticated user."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "phone": user.phone,
        "hospital_id": user.hospital_id,
        "avatar": user.avatar,
    }
