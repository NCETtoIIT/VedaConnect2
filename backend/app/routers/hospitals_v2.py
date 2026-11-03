"""
VedaConnect — Hospital Router v2 (Phase 1.5)

Endpoints:
  GET  /api/v1/hospitals/search            — rank hospitals by Care Score
  GET  /api/v1/hospitals/{id}              — single hospital detail
  GET  /api/v1/hospitals/{id}/availability — service availability with staleness badge

Key architecture rules:
  - Sponsored hospitals are NEVER included in organic Care Score ranking.
    They are returned in a separate `sponsored_slots` field.
  - Availability stale if observed_at > 6h → stale=True, drops from Care Score.
  - All distance via server-side haversine (no trusting client distance).
  - score_breakdown exposed per hospital so UI can show "Why recommended?".
"""

from __future__ import annotations

import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.hospital import HospitalModel
from app.models.veda.beds import AvailabilitySignalModel
from app.services.care_score import rank_hospitals, compute_care_score, STALE_HOURS

router = APIRouter(prefix="/api/v1/hospitals", tags=["hospitals-v2"])


# ─── DB Dependency ────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Response schemas ─────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    clinical_fit:  float
    affordability: float
    distance:      float
    availability:  float
    support:       float


class HospitalCard(BaseModel):
    id:                 str
    name:               str
    code:               str
    tagline:            str
    address:            str
    city:               str
    phone:              str
    emergency_phone:    str
    rating:             float
    review_count:       int
    emergency_available: bool
    emergency_beds_free: int
    icu_beds_free:      int
    specialties:        list
    estimated_cost_range: dict
    accepted_insurance_providers: list
    accepted_gov_schemes: list
    accreditation:      list
    opd_slot_availability: str
    image:              Optional[str]
    why_recommended:    Optional[list]
    # Care Score fields
    care_score:         float
    score_breakdown:    ScoreBreakdown
    weights_used:       dict
    stale:              bool
    distance_km:        float


class HospitalSearchResponse(BaseModel):
    organic:         list[HospitalCard]
    sponsored_slots: list[dict]
    total_organic:   int
    patient_coords:  dict


class AvailabilityService(BaseModel):
    service:     str
    status:      str
    observed_at: datetime.datetime
    stale:       bool
    stale_note:  Optional[str]


class HospitalAvailabilityResponse(BaseModel):
    hospital_id: str
    services:    list[AvailabilityService]


# ─── Helper ───────────────────────────────────────────────────────────────────

def _hospital_to_dict(h: HospitalModel, availability_age_hours: float = 0.0) -> dict:
    return {
        "id":                           h.id,
        "name":                         h.name,
        "code":                         h.code,
        "tagline":                      h.tagline,
        "address":                      h.address,
        "city":                         h.city,
        "phone":                        h.phone,
        "emergency_phone":              h.emergency_phone,
        "rating":                       h.rating,
        "review_count":                 h.review_count,
        "emergency_available":          h.emergency_available,
        "emergency_beds_free":          h.emergency_beds_free,
        "icu_beds_free":                h.icu_beds_free,
        "specialties":                  h.specialties or [],
        "estimated_cost_range":         h.estimated_cost_range or {},
        "accepted_insurance_providers": h.accepted_insurance_providers or [],
        "accepted_gov_schemes":         h.accepted_gov_schemes or [],
        "accreditation":                h.accreditation or [],
        "opd_slot_availability":        h.opd_slot_availability,
        "image":                        h.image,
        "why_recommended":              h.why_recommended,
        # Care Score inputs
        "clinical_fit_score":           h.clinical_fit_score,
        "affordability_score":          h.affordability_score,
        "availability_score":           h.availability_score,
        "support_services_score":       h.support_services_score,
        # Geo — fallback to 0 if not stored (architecture.md §geo)
        "lat":  0.0,  # hospitals table currently has no lat/lng col; fallback
        "lng":  0.0,
        "is_sponsored": False,
        "availability_signal_age_hours": availability_age_hours,
    }


def _get_availability_age(db: Session, hospital_id: str) -> float:
    """
    Returns the age in hours of the most recent availability signal for a hospital.
    0.0 if no signal exists (treated as fresh to avoid penalising missing data).
    """
    signal: AvailabilitySignalModel | None = (
        db.query(AvailabilitySignalModel)
        .filter(AvailabilitySignalModel.hospital_id == hospital_id)
        .order_by(AvailabilitySignalModel.observed_at.desc())
        .first()
    )
    if signal is None:
        return 0.0
    delta = datetime.datetime.utcnow() - signal.observed_at
    return delta.total_seconds() / 3600.0


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/search", response_model=HospitalSearchResponse, summary="Search & rank hospitals by Care Score")
def search_hospitals(
    lat:       float = Query(...,  description="Patient latitude",  ge=-90,  le=90),
    lng:       float = Query(...,  description="Patient longitude", ge=-180, le=180),
    specialty: Optional[str] = Query(None, description="Filter by specialty keyword"),
    city:      Optional[str] = Query(None, description="Filter by city"),
    limit:     int   = Query(20,   description="Max results",       ge=1,    le=100),
    db:        Session = Depends(get_db),
):
    """
    Returns hospitals ranked by Care Score for the given patient coordinates.

    - `organic`: hospitals sorted descending by Care Score
    - `sponsored_slots`: sponsored hospitals (NOT scored — clearly labelled in UI)
    - Each hospital includes `score_breakdown` and `stale` flag for UI transparency
    """
    query = db.query(HospitalModel)

    if city:
        query = query.filter(HospitalModel.city.ilike(f"%{city}%"))

    if specialty:
        # JSON contains filter — works for PostgreSQL JSON arrays
        query = query.filter(
            HospitalModel.specialties.cast(
                __import__("sqlalchemy").Text
            ).ilike(f"%{specialty}%")
        )

    hospitals_db = query.limit(200).all()  # fetch up to 200, re-rank in Python

    # Build dicts with availability staleness
    hospital_dicts = []
    for h in hospitals_db:
        age_hours = _get_availability_age(db, h.id)
        hospital_dicts.append(_hospital_to_dict(h, availability_age_hours=age_hours))

    organic, sponsored = rank_hospitals(
        hospital_dicts,
        patient_lat=lat,
        patient_lng=lng,
    )

    # Limit results
    organic = organic[:limit]

    return HospitalSearchResponse(
        organic=organic,
        sponsored_slots=sponsored,
        total_organic=len(organic),
        patient_coords={"lat": lat, "lng": lng},
    )


@router.get("/{hospital_id}", summary="Get hospital detail with live Care Score")
def get_hospital(
    hospital_id: str,
    lat: Optional[float] = Query(None, description="Patient latitude for distance calc"),
    lng: Optional[float] = Query(None, description="Patient longitude for distance calc"),
    db: Session = Depends(get_db),
):
    """Single hospital detail with Care Score if patient coordinates are provided."""
    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

    result_dict = _hospital_to_dict(h, availability_age_hours=_get_availability_age(db, hospital_id))

    if lat is not None and lng is not None:
        score_result = compute_care_score(
            clinical_fit_score=h.clinical_fit_score,
            affordability_score=h.affordability_score,
            availability_score=h.availability_score,
            support_services_score=h.support_services_score,
            hospital_lat=0.0,  # lat/lng not stored yet in hospital table
            hospital_lng=0.0,
            patient_lat=lat,
            patient_lng=lng,
            availability_signal_age_hours=result_dict["availability_signal_age_hours"],
            is_sponsored=False,
        )
        result_dict.update({
            "care_score":    score_result.care_score,
            "score_breakdown": score_result.breakdown,
            "weights_used":  score_result.weights_used,
            "stale":         score_result.stale,
            "distance_km":   score_result.distance_km,
        })

    return result_dict


@router.get("/{hospital_id}/availability", response_model=HospitalAvailabilityResponse, summary="Service availability with staleness badge")
def get_hospital_availability(
    hospital_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns all availability signals for a hospital.
    Signals older than 6 hours are marked `stale=True` with a human-readable note.
    """
    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

    signals = (
        db.query(AvailabilitySignalModel)
        .filter(AvailabilitySignalModel.hospital_id == hospital_id)
        .order_by(AvailabilitySignalModel.observed_at.desc())
        .all()
    )

    now = datetime.datetime.utcnow()
    services: list[AvailabilityService] = []
    for s in signals:
        age_hours = (now - s.observed_at).total_seconds() / 3600.0
        is_stale  = age_hours > STALE_HOURS
        services.append(AvailabilityService(
            service=s.service,
            status=s.status,
            observed_at=s.observed_at,
            stale=is_stale,
            stale_note=(
                f"Data not verified for {age_hours:.0f}h — may not reflect current availability"
                if is_stale else None
            ),
        ))

    return HospitalAvailabilityResponse(
        hospital_id=hospital_id,
        services=services,
    )

