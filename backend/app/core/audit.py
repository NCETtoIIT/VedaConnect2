"""
VedaConnect Core Audit — Append-only audit logging.

Hashes IP and User-Agent for privacy (never stores raw PII).
Uses the existing AuditLogModel from models/audit.py.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit import AuditLogModel


# ── Privacy-safe hashing ─────────────────────────────────────────

_HASH_SALT = "vedaconnect-audit-v1"  # static salt for consistent hashing


def _hash_value(value: str) -> str:
    """One-way SHA-256 hash of a value with a static salt for audit privacy."""
    if not value:
        return "unknown"
    combined = f"{_HASH_SALT}:{value}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]


def _extract_request_metadata(request: Optional[Request]) -> dict:
    """Extract and hash request metadata for audit purposes."""
    if not request:
        return {"ip_hash": "no-request", "ua_hash": "no-request"}

    client_ip = "unknown"
    if request.client and request.client.host:
        client_ip = request.client.host

    user_agent = request.headers.get("User-Agent", "unknown")

    return {
        "ip_hash": _hash_value(client_ip),
        "ua_hash": _hash_value(user_agent),
    }


# ═══════════════════════════════════════════════════════════════
#  Audit Log Function
# ═══════════════════════════════════════════════════════════════

def log_audit(
    db: Session,
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: str,
    purpose: str = "",
    request: Optional[Request] = None,
    extra: Optional[dict] = None,
) -> AuditLogModel:
    """
    Create an append-only audit log entry.

    Args:
        db: SQLAlchemy session
        actor_id: ID of the user performing the action
        actor_role: Role of the actor (PATIENT, DOCTOR, etc.)
        action: Action performed (e.g., "LOGIN", "VIEW_RECORD", "UPDATE_PATIENT")
        resource_type: Type of resource acted upon (e.g., "user", "patient", "appointment")
        resource_id: ID of the resource
        purpose: Purpose/reason for the access
        request: FastAPI Request object (for IP/UA hashing)
        extra: Additional structured metadata

    Returns:
        The created AuditLogModel instance
    """
    now = datetime.now(timezone.utc)
    req_meta = _extract_request_metadata(request)

    # Build structured details JSON
    details = {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "purpose": purpose,
        "ip_hash": req_meta["ip_hash"],
        "ua_hash": req_meta["ua_hash"],
    }
    if extra:
        details["extra"] = extra

    audit_entry = AuditLogModel(
        id=f"audit-{uuid.uuid4().hex[:12]}",
        timestamp=now.isoformat(),
        actor_role=actor_role,
        actor_id=actor_id,
        action=action,
        details=json.dumps(details),
        created_at=now,
    )

    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry
