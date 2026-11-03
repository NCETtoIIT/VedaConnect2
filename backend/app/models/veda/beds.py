"""
VedaConnect — Beds & Availability Models
Per architecture.md: beds with staleness tracking.
"""
import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.database import Base


class BedModel(Base):
    """Hospital bed counts by ward."""
    __tablename__ = "beds"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    ward = Column(String, nullable=False, comment="general, icu, nicu, maternity, etc.")
    total = Column(Integer, nullable=False, default=0)
    occupied = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AvailabilitySignalModel(Base):
    """
    Service availability with staleness tracking.
    Per rules: data older than 6h renders as "Last verified 6h ago"
    and drops from Care Score availability weight.
    """
    __tablename__ = "availability_signals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    service = Column(String, nullable=False, comment="opd, emergency, icu, lab, etc.")
    status = Column(String, nullable=False, comment="available, limited, unavailable")
    observed_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    source = Column(String, nullable=True, comment="admin_manual, api_sync, scrape")

