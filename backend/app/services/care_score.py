"""
VedaConnect — Care Score Engine (Phase 1.3)
Pure-function, zero DB calls. Can be unit-tested independently.

Weights per architecture.md / prd.md:
  clinical_fit   = 35
  affordability  = 25
  distance       = 15
  availability   = 15
  support        = 10
  TOTAL          = 100  (invariant — unit test asserts this)

Stale availability rule (architecture.md §data-freshness):
  If availability_signal_age_hours > 6 → availability weight collapses to 0,
  and its weight is redistributed proportionally to the remaining four vectors
  so the total always stays at 100.

Sponsored hospitals:
  Never included in Care Score ranking. They occupy a separate sponsored slot
  field in the API response. This function refuses to score them (raises ValueError).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

# ─── canonical weight constants ─────────────────────────────────────────────

WEIGHTS: dict[str, int] = {
    "clinical_fit":  35,
    "affordability":  25,
    "distance":       15,
    "availability":   15,
    "support":        10,
}

assert sum(WEIGHTS.values()) == 100, "Care Score weights must sum to 100"

STALE_HOURS: int = 6          # availability signal older than this → stale
DISTANCE_FULL_SCORE_KM: float = 2.0   # ≤ 2 km → 100 pts
DISTANCE_DECAY_PER_KM: float  = 5.0   # lose 5 pts per km beyond 2 km
DISTANCE_FLOOR: float          = 50.0  # floor score for any distance


# ─── result dataclass ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CareScoreResult:
    care_score:    float
    breakdown:     dict[str, float]   # each vector's weighted contribution
    weights_used:  dict[str, int]     # actual weights applied (availability may be 0)
    stale:         bool               # True if availability signal is stale
    distance_km:   float


# ─── internal helpers ────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi        = math.radians(lat2 - lat1)
    dlambda     = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _distance_score(km: float) -> float:
    """100 for ≤ 2 km, drops 5 pts/km, floor 50."""
    if km <= DISTANCE_FULL_SCORE_KM:
        return 100.0
    raw = 100.0 - (km - DISTANCE_FULL_SCORE_KM) * DISTANCE_DECAY_PER_KM
    return max(DISTANCE_FLOOR, raw)


def _redistribute_weights(skip_key: str, base_weights: dict[str, int]) -> dict[str, int]:
    """
    Remove a vector and redistribute its weight proportionally to the rest.
    Used when availability is stale — its 15pts go to the other four.
    """
    removed = base_weights[skip_key]
    remaining = {k: v for k, v in base_weights.items() if k != skip_key}
    total_remaining = sum(remaining.values())
    if total_remaining == 0:
        return {k: 0 for k in remaining}
    redistributed = {}
    allocated = 0
    keys = list(remaining.keys())
    for i, k in enumerate(keys):
        if i == len(keys) - 1:
            # last key gets the remainder to ensure exact sum = 100
            redistributed[k] = 100 - allocated
        else:
            share = round(remaining[k] / total_remaining * (total_remaining + removed))
            redistributed[k] = share
            allocated += share
    redistributed[skip_key] = 0
    return redistributed


# ─── public API ─────────────────────────────────────────────────────────────

def compute_care_score(
    *,
    # Hospital raw scores (0–100 each)
    clinical_fit_score:    float,
    affordability_score:   float,
    availability_score:    float,
    support_services_score: float,
    # Geo
    hospital_lat: float,
    hospital_lng: float,
    patient_lat:  float,
    patient_lng:  float,
    # Staleness
    availability_signal_age_hours: float = 0.0,
    # Sponsorship guard
    is_sponsored: bool = False,
) -> CareScoreResult:
    """
    Compute VedaConnect Care Score for a single hospital.

    Parameters
    ----------
    clinical_fit_score           : 0–100 — specialty/condition match quality
    affordability_score          : 0–100 — cost vs patient budget fit
    availability_score           : 0–100 — bed/slot availability quality
    support_services_score       : 0–100 — insurance, schemes, NGO support
    hospital_lat/lng             : Hospital coordinates
    patient_lat/lng              : Patient coordinates (for haversine distance)
    availability_signal_age_hours: Hours since last availability signal refresh
    is_sponsored                 : If True, raises ValueError — sponsored hospitals
                                   must NOT be in organic ranking.

    Returns
    -------
    CareScoreResult with care_score, breakdown, weights_used, stale, distance_km
    """
    if is_sponsored:
        raise ValueError(
            "Sponsored hospitals must not be included in Care Score ranking. "
            "Place them in the 'sponsored_slots' field of the API response instead."
        )

    # Clamp inputs to 0–100
    clinical_fit_score      = max(0.0, min(100.0, float(clinical_fit_score)))
    affordability_score     = max(0.0, min(100.0, float(affordability_score)))
    availability_score      = max(0.0, min(100.0, float(availability_score)))
    support_services_score  = max(0.0, min(100.0, float(support_services_score)))

    # Staleness check
    stale = float(availability_signal_age_hours) > STALE_HOURS

    # Effective weights
    if stale:
        weights_used = _redistribute_weights("availability", WEIGHTS)
    else:
        weights_used = dict(WEIGHTS)

    assert sum(weights_used.values()) == 100, "weights must sum to 100 after redistribution"

    # Distance
    dist_km    = _haversine_km(patient_lat, patient_lng, hospital_lat, hospital_lng)
    dist_score = _distance_score(dist_km)

    # Weighted contributions (contribution = raw_score * weight / 100)
    breakdown: dict[str, float] = {
        "clinical_fit":  round(clinical_fit_score     * weights_used["clinical_fit"]  / 100, 2),
        "affordability": round(affordability_score    * weights_used["affordability"] / 100, 2),
        "distance":      round(dist_score             * weights_used["distance"]      / 100, 2),
        "availability":  round((0.0 if stale else availability_score) * weights_used["availability"] / 100, 2),
        "support":       round(support_services_score * weights_used["support"]       / 100, 2),
    }

    care_score = round(sum(breakdown.values()), 1)

    return CareScoreResult(
        care_score=care_score,
        breakdown=breakdown,
        weights_used=weights_used,
        stale=stale,
        distance_km=round(dist_km, 2),
    )


def rank_hospitals(
    hospitals: list[dict[str, Any]],
    *,
    patient_lat: float,
    patient_lng: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Rank a list of hospital dicts by Care Score.

    Returns (ranked_organic, sponsored_slots).
    Sponsored hospitals (is_sponsored=True) are separated and never ranked.

    Expected keys per hospital dict:
      id, name, lat, lng,
      clinical_fit_score, affordability_score, availability_score, support_services_score,
      availability_signal_age_hours (optional, defaults to 0),
      is_sponsored (optional, defaults to False)
    """
    organic: list[dict] = []
    sponsored: list[dict] = []

    for h in hospitals:
        if h.get("is_sponsored", False):
            sponsored.append(h)
            continue

        result = compute_care_score(
            clinical_fit_score=h.get("clinical_fit_score", 80.0),
            affordability_score=h.get("affordability_score", 80.0),
            availability_score=h.get("availability_score", 80.0),
            support_services_score=h.get("support_services_score", 80.0),
            hospital_lat=float(h.get("lat", 0.0)),
            hospital_lng=float(h.get("lng", 0.0)),
            patient_lat=patient_lat,
            patient_lng=patient_lng,
            availability_signal_age_hours=float(h.get("availability_signal_age_hours", 0.0)),
            is_sponsored=False,
        )

        enriched = {
            **h,
            "care_score":    result.care_score,
            "score_breakdown": result.breakdown,
            "weights_used":  result.weights_used,
            "stale":         result.stale,
            "distance_km":   result.distance_km,
        }
        organic.append(enriched)

    organic.sort(key=lambda x: x["care_score"], reverse=True)
    return organic, sponsored

