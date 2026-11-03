"""
VedaConnect — Attachment & Analysis Models
Per architecture.md: attachments (reports, photos), OCR extractions, image assessments.
"""
import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text
from app.database import Base


class AttachmentModel(Base):
    """
    Uploaded files: reports, photos, prescriptions.
    Stored in S3-compatible storage with server-side encryption.
    """
    __tablename__ = "veda_attachments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(
        String, nullable=False,
        comment="report, photo, prescription"
    )
    storage_key = Column(String, nullable=False, comment="S3 object key")
    sha256 = Column(String, nullable=False, comment="Content hash for integrity")
    mime = Column(String, nullable=False, comment="MIME type — allowlist enforced")
    ocr_status = Column(
        String, nullable=True, default="pending",
        comment="pending, processing, done, failed"
    )
    retention_until = Column(DateTime, nullable=True, comment="Data retention deadline")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ReportExtractionModel(Base):
    """
    OCR-extracted values from medical reports.
    Per rules: PHI fields (raw_text, values) encrypted at application level.
    """
    __tablename__ = "report_extractions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attachment_id = Column(String, ForeignKey("veda_attachments.id"), nullable=False, index=True)
    raw_text = Column(Text, nullable=True, comment="Encrypted — raw OCR output")
    values = Column(JSON, nullable=True, comment="Encrypted — extracted parameters")
    confidence = Column(JSON, nullable=True, comment="Per-field confidence scores")
    ai_summary_i18n = Column(
        JSON, nullable=True,
        comment="Plain-language explanation keyed by language code"
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ImageAssessmentModel(Base):
    """
    AI image triage results — ALWAYS probabilistic, NEVER a diagnosis.
    Per rules A1: candidates with probabilities, never a single verdict.
    """
    __tablename__ = "image_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    attachment_id = Column(String, ForeignKey("veda_attachments.id"), nullable=False, index=True)
    candidates = Column(
        JSON, nullable=False,
        comment="[{condition, probability}] — probabilities must sum ~1"
    )
    confidence = Column(Float, nullable=False, comment="Overall confidence 0-1")
    urgency_band = Column(
        String, nullable=False,
        comment="now, within_24h, within_week, routine"
    )
    disclaimer_version = Column(String, nullable=False, default="1.0")
    reviewed_by_doctor = Column(
        String, nullable=True,
        comment="Doctor user_id who reviewed — never auto-accepted"
    )
    model_version = Column(String, nullable=True, comment="For reproducibility per rules C3.4")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

