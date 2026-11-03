"""
VedaConnect — Consent Model (DPDP Act 2023 compliant)
Purpose-based, granular, revocable consent per rules.md B1.
"""
import datetime
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.database import Base


class VedaConsentModel(Base):
    """
    DPDP-compliant consent records.
    Each row represents consent for ONE specific purpose+scope.
    Consent is free, specific, informed, and revocable.
    """
    __tablename__ = "veda_consents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(
        String, nullable=False,
        comment="One of: care_delivery, record_storage, research_anonymised, marketing"
    )
    scope = Column(
        String, nullable=False,
        comment="What data this consent covers, e.g. 'medical_records', 'intake_data', 'location'"
    )
    version = Column(String, nullable=False, default="1.0", comment="Consent policy version")
    granted_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    consent_text_shown = Column(Text, nullable=True, comment="Exact text shown to user at grant time")
    lang = Column(String, nullable=True, default="en", comment="Language consent was shown in")

