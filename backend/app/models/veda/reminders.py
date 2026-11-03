"""
VedaConnect — Reminder & Teleconsultation Models
"""
import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from app.database import Base


class ReminderModel(Base):
    """Medicine reminder with schedule."""
    __tablename__ = "reminders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    drug = Column(String, nullable=False)
    dose = Column(String, nullable=False)
    schedule_cron = Column(String, nullable=False, comment="Cron expression for reminder timing")
    tz = Column(String, nullable=False, default="Asia/Kolkata")
    source = Column(String, nullable=True, comment="manual or prescription_ocr")
    active = Column(Boolean, default=True)
    last_fired_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ReminderLogModel(Base):
    """Adherence tracking — opt-in only."""
    __tablename__ = "reminder_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reminder_id = Column(String, ForeignKey("reminders.id"), nullable=False, index=True)
    fired_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    status = Column(
        String, nullable=False, default="no_response",
        comment="taken, skipped, no_response"
    )


class ConsultModel(Base):
    """Teleconsultation session linked to a booking."""
    __tablename__ = "veda_consults"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, ForeignKey("veda_bookings.id"), nullable=False, index=True)
    room_id = Column(String, nullable=True, comment="LiveKit room ID")
    starts_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True, comment="Encrypted — doctor notes")
    prescription_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FeedbackModel(Base):
    """
    Patient feedback — verified-visit badge required.
    Per rules A10: only patients with discharged booking can post.
    """
    __tablename__ = "veda_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String, ForeignKey("veda_bookings.id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    rating = Column(String, nullable=False, comment="1-5 stars")
    text = Column(Text, nullable=True)
    before_after_opt_in = Column(Boolean, default=False, comment="Consent for before/after gallery")
    verified_visit = Column(Boolean, default=False, comment="True only if booking.status == discharged")
    moderation_status = Column(
        String, default="pending",
        comment="pending, approved, rejected"
    )
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

