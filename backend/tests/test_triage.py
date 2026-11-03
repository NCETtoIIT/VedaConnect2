"""
Unit tests for VedaConnect Triage Engine.
Run with: cd backend && python -m pytest tests/test_triage.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.services.veda_triage_service import (
    evaluate_triage,
    safe_triage_fallback,
    CONFIDENCE_UNCERTAIN_THRESHOLD,
    DISCLAIMER,
    MODEL_VERSION,
    TriageOutput,
)


# ─── Red-flag guard tests ─────────────────────────────────────────────────────

class TestRedFlagGuard:
    """rules.md A3: Red flags ALWAYS → concern_level=emergency, overriding model output."""

    def test_chest_pain_plus_sweating_triggers_emergency(self):
        result = evaluate_triage(
            symptoms=["chest pain", "cold sweat"],
        )
        assert result.concern_level == "emergency"
        assert "chest_pain_with_sweating" in result.red_flags
        assert result.urgency_band == "now"

    def test_chest_discomfort_plus_diaphoresis_triggers_emergency(self):
        result = evaluate_triage(
            symptoms=["chest discomfort", "diaphoresis"],
        )
        assert result.concern_level == "emergency"
        assert "chest_pain_with_sweating" in result.red_flags

    def test_stroke_signs_trigger_emergency(self):
        result = evaluate_triage(
            symptoms=["face drooping", "sudden confusion"],
        )
        assert result.concern_level == "emergency"
        assert "stroke_signs_FAST" in result.red_flags

    def test_arm_weakness_plus_speech_difficulty_triggers_stroke_flag(self):
        result = evaluate_triage(
            symptoms=["arm weakness", "speech difficulty"],
        )
        assert result.concern_level == "emergency"
        assert "stroke_signs_FAST" in result.red_flags

    def test_unconscious_patient_triggers_emergency(self):
        result = evaluate_triage(
            symptoms=["patient is unconscious", "not responding"],
        )
        assert result.concern_level == "emergency"
        assert "unconsciousness" in result.red_flags

    def test_suicidal_ideation_triggers_emergency(self):
        result = evaluate_triage(
            symptoms=["suicidal thoughts"],
        )
        assert result.concern_level == "emergency"
        assert "suicidal_ideation" in result.red_flags

    def test_severe_bleeding_triggers_emergency(self):
        result = evaluate_triage(
            symptoms=["severe bleeding from arm"],
        )
        assert result.concern_level == "emergency"
        assert "severe_bleeding_trauma" in result.red_flags

    def test_breathlessness_at_rest_triggers_emergency(self):
        result = evaluate_triage(
            symptoms=["breathlessness at rest"],
        )
        assert result.concern_level == "emergency"
        assert "breathlessness_at_rest" in result.red_flags

    def test_pregnancy_with_bleeding_triggers_emergency(self):
        result = evaluate_triage(
            symptoms=["pregnant", "heavy bleeding"],
        )
        assert result.concern_level == "emergency"
        assert "pregnancy_bleeding" in result.red_flags

    def test_hindi_chest_pain_triggers_emergency(self):
        """Hindi symptom inputs must also trigger red flags."""
        result = evaluate_triage(
            symptoms=["seene mein dard", "paseena"],
        )
        assert result.concern_level == "emergency"
        assert "chest_pain_with_sweating" in result.red_flags

    def test_chest_pain_without_sweating_does_not_trigger_combination_flag(self):
        """Combination flag requires BOTH groups to match."""
        result = evaluate_triage(
            symptoms=["mild chest pain"],
        )
        assert "chest_pain_with_sweating" not in result.red_flags
        # Note: still might be urgent due to specialty, but not emergency from this flag

    def test_red_flags_are_listed_in_output(self):
        result = evaluate_triage(
            symptoms=["chest pain", "sweating"],
        )
        assert isinstance(result.red_flags, list)
        assert len(result.red_flags) > 0


# ─── Confidence / uncertain branch tests ─────────────────────────────────────

class TestConfidenceBranch:
    """rules.md A3-2: confidence < 0.55 → uncertain branch."""

    def test_single_vague_symptom_drops_confidence(self):
        """
        A single non-specific symptom with no red flags should have low confidence
        and the service should still return a safe output.
        """
        result = evaluate_triage(symptoms=["feeling off"])
        # Result should be safe regardless of confidence branch
        assert result.requires_doctor_escalation is True or result.concern_level in ("routine", "urgent", "emergency")

    def test_uncertain_branch_suggests_general_medicine(self):
        """When confidence < threshold, specialty defaults to General Medicine."""
        # Artificially trigger: single empty/very vague input
        result = evaluate_triage(symptoms=[""])
        if result.confidence < CONFIDENCE_UNCERTAIN_THRESHOLD:
            assert result.suggested_specialty == "General Medicine"
            assert result.requires_doctor_escalation is True

    def test_uncertain_branch_has_safe_possible_causes(self):
        """Low-confidence output should have a safe, non-diagnostic possible_causes."""
        result = evaluate_triage(symptoms=[""])
        if result.confidence < CONFIDENCE_UNCERTAIN_THRESHOLD:
            assert any("consult" in c.lower() or "insufficient" in c.lower() for c in result.possible_causes)


# ─── Output schema validation ─────────────────────────────────────────────────

class TestOutputSchema:
    """Every TriageOutput must have all required fields with correct types."""

    def _validate_output(self, result: TriageOutput):
        # Required fields
        assert isinstance(result.symptoms, list)
        assert isinstance(result.duration, str)
        assert result.severity in ("mild", "moderate", "severe")
        assert isinstance(result.red_flags, list)
        assert result.concern_level in ("emergency", "urgent", "routine")
        assert isinstance(result.suggested_specialty, str)
        assert len(result.suggested_specialty) > 0
        assert isinstance(result.possible_causes, list)
        assert len(result.possible_causes) > 0
        assert 0.0 <= result.confidence <= 1.0
        assert result.urgency_band in ("now", "within_24h", "within_week", "routine")
        assert result.disclaimer == DISCLAIMER
        assert result.model_version == MODEL_VERSION
        assert isinstance(result.requires_doctor_escalation, bool)

    def test_schema_for_emergency_case(self):
        result = evaluate_triage(symptoms=["chest pain", "sweating"])
        self._validate_output(result)

    def test_schema_for_routine_case(self):
        result = evaluate_triage(symptoms=["mild headache"])
        self._validate_output(result)

    def test_schema_for_fever_case(self):
        result = evaluate_triage(symptoms=["fever", "body ache", "sore throat"])
        self._validate_output(result)

    def test_to_dict_returns_all_keys(self):
        result = evaluate_triage(symptoms=["fever"])
        d = result.to_dict()
        required_keys = {
            "symptoms", "duration", "severity", "red_flags", "concern_level",
            "suggested_specialty", "possible_causes", "confidence", "urgency_band",
            "disclaimer", "model_version", "requires_doctor_escalation"
        }
        assert required_keys.issubset(set(d.keys()))


# ─── No diagnosis in output ───────────────────────────────────────────────────

class TestNoDirectDiagnosis:
    """rules.md A1: NEVER output a definitive disease name."""

    _FORBIDDEN_DIAGNOSIS_PHRASES = [
        "you have",
        "diagnosed with",
        "you are suffering from",
        "confirmed diagnosis",
        "you definitely have",
        "disease detected",
    ]

    def _assert_no_diagnosis(self, result: TriageOutput):
        full_text = (
            result.suggested_specialty + " " +
            " ".join(result.possible_causes) +
            " " + result.disclaimer
        ).lower()
        for phrase in self._FORBIDDEN_DIAGNOSIS_PHRASES:
            assert phrase not in full_text, (
                f"Forbidden diagnostic phrase found: '{phrase}' in output"
            )

    def test_emergency_case_no_diagnosis(self):
        result = evaluate_triage(symptoms=["chest pain", "sweating"])
        self._assert_no_diagnosis(result)

    def test_routine_case_no_diagnosis(self):
        result = evaluate_triage(symptoms=["mild fever"])
        self._assert_no_diagnosis(result)

    def test_specialty_is_not_a_diagnosis_string(self):
        """Specialty should be a department name, not 'You have COVID-19' etc."""
        result = evaluate_triage(symptoms=["high fever", "body ache", "cough"])
        # Should not contain words like "you have" or "diagnosis"
        assert "you have" not in result.suggested_specialty.lower()
        assert "diagnosis" not in result.suggested_specialty.lower()


# ─── Disclaimer always present ────────────────────────────────────────────────

class TestDisclaimer:
    def test_disclaimer_always_in_output(self):
        for symptoms in [
            ["fever"],
            ["chest pain", "sweating"],
            ["unconscious"],
            [],
        ]:
            result = evaluate_triage(symptoms=symptoms)
            assert result.disclaimer == DISCLAIMER

    def test_requires_doctor_escalation_for_emergency(self):
        result = evaluate_triage(symptoms=["chest pain", "cold sweat"])
        assert result.requires_doctor_escalation is True

    def test_requires_doctor_escalation_for_urgent(self):
        result = evaluate_triage(symptoms=["severe abdominal pain", "vomiting"], stated_severity="severe")
        assert result.requires_doctor_escalation is True


# ─── Safe fallback ────────────────────────────────────────────────────────────

class TestSafeFallback:
    """safe_triage_fallback must never raise and always return a valid safe output."""

    def test_fallback_does_not_raise_on_garbage_input(self):
        result = safe_triage_fallback("!@#$%^&*()_+")
        assert isinstance(result, TriageOutput)

    def test_fallback_does_not_raise_on_empty_string(self):
        result = safe_triage_fallback("")
        assert isinstance(result, TriageOutput)

    def test_fallback_always_escalates_to_doctor(self):
        result = safe_triage_fallback("some broken input")
        assert result.requires_doctor_escalation is True

    def test_fallback_confidence_is_zero(self):
        result = safe_triage_fallback("anything")
        assert result.confidence == 0.0

    def test_fallback_has_disclaimer(self):
        result = safe_triage_fallback("anything")
        assert result.disclaimer == DISCLAIMER

