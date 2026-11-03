"""
VedaConnect — Blood Bank Models (DONATION ONLY)
Per rules A4: Blood donation only through licensed blood banks.
No price column, no checkout route, no "sell" flow — structurally enforced.
"""
import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from app.database import Base


class BloodBankModel(Base):
    """Licensed blood banks only — licence_no is required."""
    __tablename__ = "blood_banks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    licence_no = Column(String, nullable=False, comment="Required — only licensed banks")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    phone = Column(String, nullable=True)
    place_id = Column(String, nullable=True, comment="Google Places ID for map")
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BloodStockModel(Base):
    """
    Current blood stock at a licensed bank.
    NOTE: No price column exists — selling blood is prohibited in India.
    """
    __tablename__ = "blood_stock"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bank_id = Column(String, ForeignKey("blood_banks.id"), nullable=False, index=True)
    group = Column(String, nullable=False, comment="A+, A-, B+, B-, AB+, AB-, O+, O-")
    units = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class DonorModel(Base):
    """Registered blood donors — donation only, never selling."""
    __tablename__ = "donors"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    blood_group = Column(String, nullable=False)
    last_donation_at = Column(DateTime, nullable=True)
    eligibility_status = Column(
        String, default="eligible",
        comment="eligible, cooling_off, ineligible"
    )
    consent_share = Column(Boolean, default=False, comment="Can bank contact for requests")


class BloodRequestModel(Base):
    """
    Blood requests routed to banks and eligible donors.
    No payment step anywhere — this is structurally enforced.
    """
    __tablename__ = "blood_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    booking_id = Column(String, ForeignKey("veda_bookings.id"), nullable=True)
    group = Column(String, nullable=False, comment="Required blood group")
    units = Column(Integer, nullable=False, default=1)
    urgency = Column(String, nullable=False, default="normal", comment="normal, urgent, critical")
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=True)
    status = Column(String, default="open", comment="open, partially_fulfilled, fulfilled, cancelled")
    fulfilled_by_bank_id = Column(String, ForeignKey("blood_banks.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

