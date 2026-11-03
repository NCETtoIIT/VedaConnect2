"""
VedaConnect — Enhanced Audit Log (append-only, DPDP compliant)
Per rules.md B4: Every PHI read/write → audit row.
No UPDATE, no DELETE grants for app role.
"""
import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Text
from app.database import Base


class VedaAuditLogModel(Base):
    """
    Append-only audit log for PHI access tracking.
    Patient can view via "Who accessed my data" screen.
    """
    __tablename__ = "veda_audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id = Column(String, nullable=False, index=True)
    actor_role = Column(String, nullable=False)
    action = Column(
        String, nullable=False,
        comment="read, write, update, delete, export"
    )
    resource_type = Column(
        String, nullable=False, index=True,
        comment="patients, intakes, reports, consultations, etc."
    )
    resource_id = Column(String, nullable=False, index=True)
    purpose = Column(
        String, nullable=False,
        comment="care_delivery, admin_review, patient_request, audit, etc."
    )
    ip_hash = Column(String, nullable=True, comment="SHA-256 of client IP — never raw IP")
    ua_hash = Column(String, nullable=True, comment="SHA-256 of User-Agent — never raw")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

