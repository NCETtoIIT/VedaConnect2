"""
Unit tests for VedaConnect Care Score engine.
Run with: cd backend && python -m pytest tests/test_care_score.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.services.care_score import (
    compute_care_score,
    rank_hospitals,
    WEIGHTS,
    STALE_HOURS,
    _haversine_km,
    _distance_score,
    _redistribute_weights,
    CareScoreResult,
)


# ─── Invariant tests ─────────────────────────────────────────────────────────

class TestWeightInvariant:
    def test_base_weights_sum_to_100(self):
        assert sum(WEIGHTS.values()) == 100

    def test_redistributed_weights_sum_to_100(self):
        redistributed = _redistribute_weights("availability", WEIGHTS)
        assert sum(redistributed.values()) == 100

    def test_redistributed_availability_weight_is_zero(self):
        redistributed = _redistribute_weights("availability", WEIGHTS)
        assert redistributed["availability"] == 0

    def test_stale_result_weights_sum_to_100(self):
        """When availability is stale, returned weights_used must still sum to 100."""
        result = compute_care_score(
            clinical_fit_score=80.0,
            affordability_score=80.0,
            availability_score=80.0,
            support_services_score=80.0,
            hospital_lat=28.6139,
            hospital_lng=77.2090,
            patient_lat=28.6100,
            patient_lng=77.2100,
            availability_signal_age_hours=float(STALE_HOURS + 1),
        )
        assert sum(result.weights_used.values()) == 100
        assert result.stale is True

    def test_fresh_result_weights_sum_to_100(self):
        result = compute_care_score(
            clinical_fit_score=90.0,
            affordability_score=70.0,
            availability_score=85.0,
            support_services_score=60.0,
            hospital_lat=28.6139,
            hospital_lng=77.2090,
            patient_lat=28.6100,
            patient_lng=77.2100,
            availability_signal_age_hours=2.0,
        )
        assert sum(result.weights_used.values()) == 100
        assert result.stale is False


# ─── Score breakdown tests ────────────────────────────────────────────────────

class TestScoreBreakdown:
    def _base_result(self, **overrides) -> CareScoreResult:
        defaults = dict(
            clinical_fit_score=80.0,
            affordability_score=80.0,
            availability_score=80.0,
            support_services_score=80.0,
            hospital_lat=28.6139,
            hospital_lng=77.2090,
            patient_lat=28.6139,     # same location → 0 km → distance=100
            patient_lng=77.2090,
            availability_signal_age_hours=0.0,
        )
        defaults.update(overrides)
        return compute_care_score(**defaults)

    def test_breakdown_has_all_five_vectors(self):
        result = self._base_result()
        keys = set(result.breakdown.keys())
        assert keys == {"clinical_fit", "affordability", "distance", "availability", "support"}

    def test_clinical_fit_contributes_35pct(self):
        # score 100 * weight 35 / 100 = 35.0
        result = self._base_result(clinical_fit_score=100.0)
        assert result.breakdown["clinical_fit"] == pytest.approx(35.0, abs=0.5)

    def test_affordability_contributes_25pct(self):
        result = self._base_result(affordability_score=100.0)
        assert result.breakdown["affordability"] == pytest.approx(25.0, abs=0.5)

    def test_availability_contributes_15pct(self):
        result = self._base_result(availability_score=100.0)
        assert result.breakdown["availability"] == pytest.approx(15.0, abs=0.5)

    def test_support_contributes_10pct(self):
        result = self._base_result(support_services_score=100.0)
        assert result.breakdown["support"] == pytest.approx(10.0, abs=0.5)

    def test_all_100_gives_perfect_score(self):
        result = self._base_result(
            clinical_fit_score=100.0,
            affordability_score=100.0,
            availability_score=100.0,
            support_services_score=100.0,
        )
        # Distance also 100 because same coords → care_score should equal 100
        assert result.care_score == pytest.approx(100.0, abs=0.5)

    def test_care_score_equals_sum_of_breakdown(self):
        result = self._base_result(
            clinical_fit_score=75.0,
            affordability_score=60.0,
            availability_score=50.0,
            support_services_score=90.0,
        )
        assert result.care_score == pytest.approx(sum(result.breakdown.values()), abs=0.15)


# ─── Stale availability tests ─────────────────────────────────────────────────

class TestStaleAvailability:
    def test_stale_flag_set_when_age_exceeds_threshold(self):
        result = compute_care_score(
            clinical_fit_score=80.0, affordability_score=80.0,
            availability_score=80.0, support_services_score=80.0,
            hospital_lat=28.0, hospital_lng=77.0,
            patient_lat=28.0, patient_lng=77.0,
            availability_signal_age_hours=7.0,
        )
        assert result.stale is True

    def test_stale_flag_not_set_when_age_within_threshold(self):
        result = compute_care_score(
            clinical_fit_score=80.0, affordability_score=80.0,
            availability_score=80.0, support_services_score=80.0,
            hospital_lat=28.0, hospital_lng=77.0,
            patient_lat=28.0, patient_lng=77.0,
            availability_signal_age_hours=5.9,
        )
        assert result.stale is False

    def test_stale_availability_contribution_is_zero(self):
        result = compute_care_score(
            clinical_fit_score=80.0, affordability_score=80.0,
            availability_score=100.0, support_services_score=80.0,
            hospital_lat=28.0, hospital_lng=77.0,
            patient_lat=28.0, patient_lng=77.0,
            availability_signal_age_hours=8.0,
        )
        assert result.breakdown["availability"] == 0.0
        assert result.stale is True

    def test_exactly_at_threshold_is_not_stale(self):
        """Exactly 6 hours is NOT stale — must be strictly greater than."""
        result = compute_care_score(
            clinical_fit_score=80.0, affordability_score=80.0,
            availability_score=80.0, support_services_score=80.0,
            hospital_lat=28.0, hospital_lng=77.0,
            patient_lat=28.0, patient_lng=77.0,
            availability_signal_age_hours=6.0,
        )
        assert result.stale is False


# ─── Distance scoring tests ───────────────────────────────────────────────────

class TestDistanceScoring:
    def test_same_location_gives_100_distance_score(self):
        score = _distance_score(0.0)
        assert score == 100.0

    def test_under_2km_gives_100(self):
        assert _distance_score(1.5) == 100.0
        assert _distance_score(2.0) == 100.0

    def test_at_2km_gives_100(self):
        assert _distance_score(2.0) == 100.0

    def test_decay_5pts_per_km_after_2km(self):
        # 4km → 100 - (4-2)*5 = 90
        assert _distance_score(4.0) == pytest.approx(90.0, abs=0.1)

    def test_floor_at_50(self):
        # very far: 100 km → 100 - 98*5 = -390 → floor at 50
        assert _distance_score(100.0) == pytest.approx(50.0, abs=0.1)

    def test_haversine_known_distance(self):
        """Delhi → Gurgaon is approximately 24–28km (haversine straight-line)."""
        km = _haversine_km(28.6139, 77.2090, 28.4595, 77.0266)
        assert 20.0 < km < 35.0

    def test_distance_contributes_correctly_to_care_score(self):
        """Same lat/lng → distance_km=0 → distance_score=100 → contribution=15."""
        result = compute_care_score(
            clinical_fit_score=0.0,
            affordability_score=0.0,
            availability_score=0.0,
            support_services_score=0.0,
            hospital_lat=28.0,
            hospital_lng=77.0,
            patient_lat=28.0,
            patient_lng=77.0,
        )
        # Only distance contributes: 100 * 15% = 15
        assert result.breakdown["distance"] == pytest.approx(15.0, abs=0.5)


# ─── Sponsored hospital guard ────────────────────────────────────────────────

class TestSponsoredGuard:
    def test_sponsored_hospital_raises_value_error(self):
        with pytest.raises(ValueError, match="Sponsored"):
            compute_care_score(
                clinical_fit_score=90.0,
                affordability_score=90.0,
                availability_score=90.0,
                support_services_score=90.0,
                hospital_lat=28.0,
                hospital_lng=77.0,
                patient_lat=28.0,
                patient_lng=77.0,
                is_sponsored=True,
            )


# ─── rank_hospitals tests ────────────────────────────────────────────────────

class TestRankHospitals:
    def _make_hospital(self, id: str, clinical: float, sponsored: bool = False) -> dict:
        return {
            "id": id,
            "name": f"Hospital {id}",
            "lat": 28.6100,
            "lng": 77.2100,
            "clinical_fit_score": clinical,
            "affordability_score": 80.0,
            "availability_score": 80.0,
            "support_services_score": 80.0,
            "availability_signal_age_hours": 0.0,
            "is_sponsored": sponsored,
        }

    def test_hospitals_sorted_descending_by_care_score(self):
        hospitals = [
            self._make_hospital("A", clinical=60.0),
            self._make_hospital("B", clinical=90.0),
            self._make_hospital("C", clinical=75.0),
        ]
        organic, _ = rank_hospitals(hospitals, patient_lat=28.61, patient_lng=77.21)
        scores = [h["care_score"] for h in organic]
        assert scores == sorted(scores, reverse=True)

    def test_sponsored_hospitals_separated(self):
        hospitals = [
            self._make_hospital("A", clinical=90.0, sponsored=False),
            self._make_hospital("S", clinical=99.0, sponsored=True),
        ]
        organic, sponsored = rank_hospitals(hospitals, patient_lat=28.61, patient_lng=77.21)
        assert len(organic) == 1
        assert len(sponsored) == 1
        assert organic[0]["id"] == "A"
        assert sponsored[0]["id"] == "S"
        # Sponsored must not have care_score key (was not computed)
        assert "care_score" not in sponsored[0]

    def test_each_result_has_score_breakdown(self):
        hospitals = [self._make_hospital("A", clinical=80.0)]
        organic, _ = rank_hospitals(hospitals, patient_lat=28.61, patient_lng=77.21)
        assert "score_breakdown" in organic[0]
        assert set(organic[0]["score_breakdown"].keys()) == {
            "clinical_fit", "affordability", "distance", "availability", "support"
        }
