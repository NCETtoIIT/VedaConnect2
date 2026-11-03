"""
VedaConnect — Refresh Token Model with Rotation & Family Reuse Detection
Per rules.md B3: Refresh tokens have 7-day TTL with rotation + reuse detection.
If a revoked token is presented, revoke the entire token family.
"""
import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from app.database import Base


class RefreshTokenModel(Base):
    """
    Refresh tokens with family grouping for rotation and reuse detection.
    """
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    family_id = Column(String, nullable=False, index=True, comment="UUID identifying the login session family")
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_refresh_family_revoked", "family_id", "revoked"),
    )

