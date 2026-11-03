"""
VedaConnect — Bookings Router (Phase 1.6)

Hashed QR Token design (architecture.md §security):
  - ref_id  : VC-2026-XXXXX — printed on QR code. Human-readable, safe to expose.
  - token   : 32-byte random hex — returned ONCE to the booking creator. Never stored raw.
  - qr_token_hash: SHA-256(token) — stored in DB. Validate by hashing incoming token and comparing.
  - Raw token never appears in logs, analytics, audit records.

Journey events are appended on each status transition (OPD check-in, admitted, discharged).
Each event is immutable (no UPDATE) — append-only audit trail per rules.md.

Endpoints:
  POST  /api/v1/bookings               — create booking, returns one-time raw token
  GET   /api/v1/bookings/{id}          — get booking by ID
  POST  /api/v1/bookings/{id}/cancel   — cancel (patient or admin only)
  POST  /api/v1/bookings/{id}/checkin  — OPD check-in (staff/doctor only)
  GET   /api/v1/bookings/me            — my bookings (patient)
  POST  /api/v1/bookings/verify-token  — verify QR token (staff only)
"""

from __future__ import annotations

import datetime
import hashlib
import random
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import SessionLocal
from app.models.veda.booking import VedaBookingModel, JourneyEventModel
from app.models.hospital import HospitalModel
from app.models.doctor import DoctorModel

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


# ─── DB Dependency ────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_ref_id() -> str:
    """e.g. VC-2026-A3F8B — 5 uppercase alphanumeric chars."""
    year = datetime.datetime.utcnow().year
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"VC-{year}-{suffix}"


def _hash_token(token: str) -> str:
    """SHA-256 of the raw token. Raw token is never stored."""
    return hashlib.sha256(token.encode()).hexdigest()


def _append_journey_event(
    db: Session,
    booking_id: str,
    actor_id: str,
    event_type: str,
    payload: dict | None = None,
) -> JourneyEventModel:
    import uuid
    event = JourneyEventModel(
        id=str(uuid.uuid4()),
        booking_id=booking_id,
        type=event_type,
        payload_json=payload or {},
        actor_id=actor_id,
    )
    db.add(event)
    return event


# ─── Request / Response schemas ──────────────────────────────────────────────

class CreateBookingRequest(BaseModel):
    hospital_id: str
    doctor_id:   str | None = None
    slot_at:     datetime.datetime | None = None
    token_no:    int | None = None


class CreateBookingResponse(BaseModel):
    id:         str
    ref_id:     str
    status:     str
    raw_token:  str  = Field(description="One-time token. Store client-side for QR generation. NOT stored on server.")
    slot_at:    datetime.datetime | None
    hospital_id: str
    note:       str


class BookingResponse(BaseModel):
    id:          str
    ref_id:      str
    status:      str
    patient_id:  str
    hospital_id: str
    doctor_id:   str | None
    slot_at:     datetime.datetime | None
    token_no:    int | None
    created_at:  datetime.datetime
    updated_at:  datetime.datetime


class VerifyTokenRequest(BaseModel):
    token:   str = Field(description="Raw QR token provided by the patient")
    ref_id:  str = Field(description="ref_id shown on the QR code")


class VerifyTokenResponse(BaseModel):
    valid:      bool
    booking_id: str | None
    status:     str | None
    patient_id: str | None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", response_model=CreateBookingResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a booking — returns one-time raw QR token")
def create_booking(
    body:    CreateBookingRequest,
    current_user = Depends(get_current_user),
    db:      Session = Depends(get_db),
):
    """
    Creates a booking. The `raw_token` in the response is shown ONCE and never stored raw.
    The client should use it to generate a QR code. Verification uses the hashed token.
    """
    # Validate hospital
    hospital = db.query(HospitalModel).filter(HospitalModel.id == body.hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

    # Validate doctor (optional)
    if body.doctor_id:
        doctor = db.query(DoctorModel).filter(DoctorModel.id == body.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    # Generate unique ref_id (retry on collision)
    import uuid
    for _ in range(5):
        ref_id = _generate_ref_id()
        exists = db.query(VedaBookingModel).filter(VedaBookingModel.ref_id == ref_id).first()
        if not exists:
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate unique booking reference. Please try again.")

    # Generate raw token (32-byte hex)
    raw_token = secrets.token_hex(32)
    token_hash = _hash_token(raw_token)

    booking = VedaBookingModel(
        id=str(uuid.uuid4()),
        patient_id=current_user.id,
        hospital_id=body.hospital_id,
        doctor_id=body.doctor_id,
        slot_at=body.slot_at,
        token_no=body.token_no,
        status="prebooked",
        ref_id=ref_id,
        qr_token_hash=token_hash,
    )
    db.add(booking)

    # Append journey event
    _append_journey_event(db, booking.id, current_user.id, "prebooked", {
        "hospital_id": body.hospital_id,
        "slot_at": body.slot_at.isoformat() if body.slot_at else None,
    })

    db.commit()
    db.refresh(booking)

    return CreateBookingResponse(
        id=booking.id,
        ref_id=booking.ref_id,
        status=booking.status,
        raw_token=raw_token,
        slot_at=booking.slot_at,
        hospital_id=booking.hospital_id,
        note="Keep this token safe — it is shown once and cannot be recovered. Use it to generate your QR code.",
    )


@router.get("/me", summary="My bookings (patient)")
def my_bookings(
    current_user = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """Returns all bookings for the currently authenticated patient."""
    bookings = (
        db.query(VedaBookingModel)
        .filter(VedaBookingModel.patient_id == current_user.id)
        .order_by(VedaBookingModel.created_at.desc())
        .all()
    )
    return [
        BookingResponse(
            id=b.id,
            ref_id=b.ref_id,
            status=b.status,
            patient_id=b.patient_id,
            hospital_id=b.hospital_id,
            doctor_id=b.doctor_id,
            slot_at=b.slot_at,
            token_no=b.token_no,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in bookings
    ]


@router.get("/{booking_id}", response_model=BookingResponse, summary="Get booking by ID")
def get_booking(
    booking_id:   str,
    current_user = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    booking = db.query(VedaBookingModel).filter(VedaBookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # IDOR guard: patient can only see their own booking
    if current_user.role == "patient" and booking.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return BookingResponse(
        id=booking.id,
        ref_id=booking.ref_id,
        status=booking.status,
        patient_id=booking.patient_id,
        hospital_id=booking.hospital_id,
        doctor_id=booking.doctor_id,
        slot_at=booking.slot_at,
        token_no=booking.token_no,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


@router.post("/{booking_id}/cancel", summary="Cancel a booking")
def cancel_booking(
    booking_id:   str,
    current_user = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    booking = db.query(VedaBookingModel).filter(VedaBookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Only patient (owner) or admin can cancel
    if current_user.role == "patient" and booking.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if booking.status in ("discharged", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking with status '{booking.status}'",
        )

    booking.status = "cancelled"
    _append_journey_event(db, booking.id, current_user.id, "cancelled")
    db.commit()

    return {"id": booking.id, "ref_id": booking.ref_id, "status": "cancelled"}


@router.post("/{booking_id}/checkin", summary="OPD check-in (staff)")
def checkin_booking(
    booking_id:   str,
    current_user = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """
    Marks the patient as checked in. Only hospital_staff, doctor, or admin can call this.
    Patients cannot check themselves in (prevents abuse).
    """
    if current_user.role not in ("hospital_staff", "doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital staff or doctors can perform check-in",
        )

    booking = db.query(VedaBookingModel).filter(VedaBookingModel.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != "prebooked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in a booking with status '{booking.status}'",
        )

    booking.status = "checked_in"
    _append_journey_event(db, booking.id, current_user.id, "opd", {
        "checked_in_by": current_user.id,
        "checked_in_at": datetime.datetime.utcnow().isoformat(),
    })
    db.commit()

    return {"id": booking.id, "ref_id": booking.ref_id, "status": "checked_in"}


@router.post("/verify-token", response_model=VerifyTokenResponse, summary="Verify QR token (staff)")
def verify_qr_token(
    body:         VerifyTokenRequest,
    current_user = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """
    Staff scan QR code → extract token + ref_id → POST here to verify.
    Compares SHA-256(token) against stored hash. Raw token never logged.
    """
    if current_user.role not in ("hospital_staff", "doctor", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital staff can verify QR tokens",
        )

    booking = db.query(VedaBookingModel).filter(VedaBookingModel.ref_id == body.ref_id).first()
    if not booking:
        return VerifyTokenResponse(valid=False, booking_id=None, status=None, patient_id=None)

    # Constant-time comparison via hashlib (avoids timing attacks)
    submitted_hash = _hash_token(body.token)
    token_valid = secrets.compare_digest(submitted_hash, booking.qr_token_hash or "")

    if not token_valid:
        return VerifyTokenResponse(valid=False, booking_id=None, status=None, patient_id=None)

    return VerifyTokenResponse(
        valid=True,
        booking_id=booking.id,
        status=booking.status,
        patient_id=booking.patient_id,
    )
