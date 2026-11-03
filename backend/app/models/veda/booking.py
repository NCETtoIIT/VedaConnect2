"""
VedaConnect — Booking & Journey Models
Per architecture.md: bookings with journey events, hashed QR tokens.
"""
import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from app.database import Base


class VedaBookingModel(Base):
    """
    Patient booking for hospital visit.
    ref_id is the only identifier on QR — raw token never stored.
    """
    __tablename__ = "veda_bookings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=True, index=True)
    slot_at = Column(DateTime, nullable=True)
    token_no = Column(Integer, nullable=True)
    status = Column(
        String, nullable=False, default="prebooked",
        comment="prebooked, checked_in, in_consult, admitted, discharged, cancelled"
    )
    ref_id = Column(
        String, unique=True, nullable=False, index=True,
        comment="e.g. VC-2026-A3F8B — printed on QR"
    )
    qr_token_hash = Column(
        String, nullable=True,
        comment="SHA-256 of the actual token — raw token never stored"
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class JourneyEventModel(Base):
    """
    Care journey events: OPD → bed → medication → discharge.
    Each event is an immutable record.
    """
    __tablename__ = "journey_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, ForeignKey("veda_bookings.id"), nullable=False, index=True)
    type = Column(
        String, nullable=False,
        comment="opd, bed, medication, procedure, discharge"
    )
    payload_json = Column(JSON, nullable=True)
    actor_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

