"""
VedaConnect — Veda Triage Service (Phase 1.4)

Implements a DETERMINISTIC RED-FLAG GUARD that runs BEFORE any AI/model call.
Per rules.md A1, A2, A3:
  - NEVER produces a definitive disease name — only "possible causes" (probabilistic)
  - Red flags ALWAYS → concern_level="emergency", overriding any model output
  - confidence < 0.55 → forces "uncertain, consult a doctor" branch
  - Output always includes a mandatory disclaimer + requires_doctor_escalation flag

Safe output contract (JSON schema strictly):
{
  "symptoms":                 [str, ...],
  "duration":                 str,
  "severity":                 "mild" | "moderate" | "severe",
  "red_flags":                [str, ...],         # triggered red flag labels
  "concern_level":            "emergency" | "urgent" | "routine",
  "suggested_specialty":      str,               # NEVER a diagnosis string
  "possible_causes":          [str, ...],        # probabilistic, not definitive
  "confidence":               float (0.0–1.0),
  "urgency_band":             "now" | "within_24h" | "within_week" | "routine",
  "disclaimer":               str,
  "model_version":            str,
  "requires_doctor_escalation": bool
}

LEGAL / CLINICAL NOTE (rules.md A1):
  This system produces informational triage support only.
  It does NOT diagnose, prescribe, or replace a qualified medical professional.
  All outputs must be accompanied by the disclaimer and the doctor CTA.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any

# ─── constants ──────────────────────────────────────────────────────────────

MODEL_VERSION = "rule_based_v1"
DISCLAIMER = (
    "This is an informational triage assessment only — not a diagnosis. "
    "Always consult a qualified doctor before making any medical decision."
)
CONFIDENCE_UNCERTAIN_THRESHOLD = 0.55


# ─── red-flag definitions (rules.md A3) ─────────────────────────────────────
# Each entry: (label, [trigger_patterns], requires_combination)
# requires_combination=True  → ALL sub-lists must have ≥1 match
# requires_combination=False → ANY keyword in patterns triggers

_RED_FLAGS: list[dict] = [
    {
        "label": "chest_pain_with_sweating",
        "combination": True,
        "groups": [
            ["chest pain", "chest discomfort", "chhati mein dard", "seene mein dard", "heart pain"],
            ["sweating", "diaphoresis", "cold sweat", "paseena", "sweaty"],
        ],
    },
    {
        "label": "stroke_signs_FAST",
        "combination": False,
        "patterns": [
            "face drooping", "arm weakness", "speech difficulty",
            "sudden confusion", "sudden headache", "loss of vision",
            "stroke", "paralysis", "chehre ka tedha hona",
        ],
    },
    {
        "label": "severe_bleeding_trauma",
        "combination": False,
        "patterns": [
            "severe bleeding", "heavy blood loss", "trauma", "accident", "major injury",
            "gash", "hemorrhage", "khoon zyada",
        ],
    },
    {
        "label": "breathlessness_at_rest",
        "combination": False,
        "patterns": [
            "breathlessness at rest", "cannot complete sentence", "cannot speak",
            "choking", "saans nahi aa raha", "struggling to breathe",
            "cannot breathe", "respiratory distress",
        ],
    },
    {
        "label": "unconsciousness",
        "combination": False,
        "patterns": [
            "unconscious", "unresponsive", "fainted", "collapsed",
            "not responding", "behosh", "gir gaya",
        ],
    },
    {
        "label": "suicidal_ideation",
        "combination": False,
        "patterns": [
            "suicidal", "want to die", "end my life", "self harm",
            "khud ko nuksaan", "jeena nahi chahta",
        ],
    },
    {
        "label": "pregnancy_bleeding",
        "combination": True,
        "groups": [
            ["pregnant", "pregnancy", "garbhavati", "expecting"],
            ["bleeding", "blood", "spotting", "cramping"],
        ],
    },
]


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _check_red_flags(symptom_text: str) -> list[str]:
    """Return list of triggered red-flag labels."""
    t = _normalize(symptom_text)
    triggered: list[str] = []

    for flag in _RED_FLAGS:
        if flag.get("combination"):
            # ALL groups must match
            if all(any(p in t for p in grp) for grp in flag["groups"]):
                triggered.append(flag["label"])
        else:
            if any(p in t for p in flag["patterns"]):
                triggered.append(flag["label"])

    return triggered


# ─── specialty routing ───────────────────────────────────────────────────────

_SPECIALTY_RULES: list[dict] = [
    {"keywords": ["chest", "heart", "cardiac", "chhati"],          "specialty": "Cardiology"},
    {"keywords": ["stroke", "paralysis", "face droop", "speech"],  "specialty": "Neurology / Emergency"},
    {"keywords": ["breathless", "asthma", "saans", "lung"],        "specialty": "Pulmonology"},
    {"keywords": ["stomach", "abdomen", "ulcer", "vomit", "pet"], "specialty": "Gastroenterology"},
    {"keywords": ["fever", "bukhar", "cold", "flu", "infection"],  "specialty": "General Medicine"},
    {"keywords": ["bone", "fracture", "joint", "knee", "spine"],   "specialty": "Orthopedics"},
    {"keywords": ["skin", "rash", "itching", "allergy"],           "specialty": "Dermatology"},
    {"keywords": ["eye", "vision", "aankh"],                       "specialty": "Ophthalmology"},
    {"keywords": ["ear", "hearing", "throat", "nose", "kaan"],     "specialty": "ENT"},
    {"keywords": ["pregnancy", "pregnant", "garbhavati"],          "specialty": "Obstetrics & Gynecology"},
    {"keywords": ["mental", "anxiety", "depression", "suicidal"],  "specialty": "Psychiatry"},
    {"keywords": ["child", "bacha", "infant", "pediatric"],        "specialty": "Pediatrics"},
]

_POSSIBLE_CAUSES: dict[str, list[str]] = {
    "Cardiology": [
        "Possible cardiac event (evaluation needed)",
        "Musculoskeletal chest pain",
        "Acid reflux / GERD",
    ],
    "Neurology / Emergency": [
        "Possible cerebrovascular event (evaluation needed)",
        "Migraine",
        "Tension headache",
    ],
    "Pulmonology": [
        "Possible respiratory tract infection",
        "Asthma exacerbation",
        "Anxiety-related breathing difficulty",
    ],
    "Gastroenterology": [
        "Possible gastritis or peptic ulcer",
        "Irritable bowel syndrome",
        "Food intolerance",
    ],
    "General Medicine": [
        "Viral / bacterial infection",
        "Dengue / malaria (if in endemic area)",
        "Seasonal flu",
    ],
    "Orthopedics": [
        "Musculoskeletal strain",
        "Possible fracture (X-ray needed)",
        "Arthritis flare",
    ],
    "Dermatology": [
        "Allergic reaction",
        "Eczema / psoriasis",
        "Contact dermatitis",
    ],
    "Ophthalmology": [
        "Conjunctivitis",
        "Refractive error",
        "Possible glaucoma (assessment needed)",
    ],
    "ENT": [
        "Upper respiratory tract infection",
        "Pharyngitis / tonsillitis",
        "Otitis media",
    ],
    "Obstetrics & Gynecology": [
        "Pregnancy-related condition (immediate evaluation needed)",
        "Threatened abortion (evaluation needed)",
        "Ectopic pregnancy (rule out)",
    ],
    "Psychiatry": [
        "Anxiety disorder",
        "Depressive episode",
        "Acute stress reaction",
    ],
    "Pediatrics": [
        "Febrile illness",
        "Upper respiratory infection",
        "Gastrointestinal infection",
    ],
}

_DEFAULT_SPECIALTY = "General Medicine"


def _infer_specialty(symptom_text: str) -> str:
    t = _normalize(symptom_text)
    for rule in _SPECIALTY_RULES:
        if any(kw in t for kw in rule["keywords"]):
            return rule["specialty"]
    return _DEFAULT_SPECIALTY


def _infer_severity(symptom_text: str, stated_severity: str | None) -> str:
    """Normalize to mild / moderate / severe."""
    if stated_severity:
        sv = stated_severity.lower()
        if sv in ("severe", "high", "critical", "emergency"):
            return "severe"
        if sv in ("moderate", "medium"):
            return "moderate"
        if sv in ("mild", "low", "minor"):
            return "mild"
    t = _normalize(symptom_text)
    if any(w in t for w in ["severe", "intense", "excruciating", "worst", "unbearable"]):
        return "severe"
    if any(w in t for w in ["moderate", "significant", "considerable"]):
        return "moderate"
    return "mild"


def _infer_confidence(
    symptoms: list[str],
    red_flags: list[str],
    specialty: str,
    severity: str,
) -> float:
    """
    Rule-based confidence heuristic (0.0–1.0).
    Real model integration will replace this; for now it signals uncertainty
    correctly so the uncertain branch is triggered when appropriate.
    """
    base = 0.65
    if len(symptoms) >= 3:
        base += 0.10
    if red_flags:
        base += 0.15          # red flags are high-signal
    if severity == "severe":
        base += 0.05
    if len(symptoms) == 1 and not red_flags:
        base -= 0.15          # single vague symptom → lower confidence
    return round(min(1.0, max(0.0, base)), 2)


# ─── output dataclass ────────────────────────────────────────────────────────

@dataclass
class TriageOutput:
    symptoms:                  list[str]
    duration:                  str
    severity:                  str
    red_flags:                 list[str]
    concern_level:             str
    suggested_specialty:       str
    possible_causes:           list[str]
    confidence:                float
    urgency_band:              str
    disclaimer:                str
    model_version:             str
    requires_doctor_escalation: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─── public API ─────────────────────────────────────────────────────────────

def evaluate_triage(
    symptoms: list[str],
    duration: str = "unknown",
    stated_severity: str | None = None,
    medical_history: list[str] | None = None,
) -> TriageOutput:
    """
    Deterministic triage engine.

    Parameters
    ----------
    symptoms        : List of symptom strings (patient-reported)
    duration        : Duration string (e.g. "2 days", "1 hour")
    stated_severity : Optional patient-stated severity ("mild"/"moderate"/"severe")
    medical_history : Optional list of known conditions

    Returns
    -------
    TriageOutput — always includes disclaimer and requires_doctor_escalation

    Rules (per rules.md A3):
    1. Red-flag guard runs first — if ANY red flag triggered → concern_level=emergency
    2. confidence < 0.55 → uncertain branch (concern_level stays, but specialty = "General Medicine", possible_causes unclear)
    3. No definitive disease name ever — only probabilistic possible_causes
    """
    if medical_history is None:
        medical_history = []

    # Combine all text for pattern matching
    symptom_text = " ".join(symptoms + medical_history)

    # ── STEP 1: Deterministic red-flag guard (runs BEFORE any model) ──────
    red_flags = _check_red_flags(symptom_text)

    # ── STEP 2: Specialty inference ───────────────────────────────────────
    specialty = _infer_specialty(symptom_text)

    # ── STEP 3: Severity ─────────────────────────────────────────────────
    severity = _infer_severity(symptom_text, stated_severity)

    # ── STEP 4: Confidence ───────────────────────────────────────────────
    confidence = _infer_confidence(symptoms, red_flags, specialty, severity)

    # ── STEP 5: Apply rules.md A3 constraints ────────────────────────────

    # Rule A3-1: Red flags ALWAYS → emergency (cannot be overridden)
    if red_flags:
        concern_level = "emergency"
        urgency_band  = "now"
    elif confidence < CONFIDENCE_UNCERTAIN_THRESHOLD:
        # Rule A3-2: Low confidence → uncertain branch
        concern_level = "routine"
        urgency_band  = "within_week"
        specialty     = "General Medicine"
    elif severity == "severe":
        concern_level = "urgent"
        urgency_band  = "within_24h"
    elif severity == "moderate":
        concern_level = "urgent"
        urgency_band  = "within_24h"
    else:
        concern_level = "routine"
        urgency_band  = "within_week"

    # ── STEP 6: Possible causes (probabilistic, NEVER definitive) ────────
    if confidence < CONFIDENCE_UNCERTAIN_THRESHOLD:
        possible_causes = [
            "Insufficient symptom information for reliable assessment.",
            "Please consult a doctor for a thorough evaluation.",
        ]
    else:
        possible_causes = _POSSIBLE_CAUSES.get(specialty, [
            "Multiple possible conditions — requires clinical evaluation.",
        ])

    # ── STEP 7: doctor escalation flag ───────────────────────────────────
    requires_doctor_escalation = (
        bool(red_flags)
        or concern_level in ("emergency", "urgent")
        or confidence < CONFIDENCE_UNCERTAIN_THRESHOLD
    )

    return TriageOutput(
        symptoms=list(symptoms),
        duration=duration,
        severity=severity,
        red_flags=red_flags,
        concern_level=concern_level,
        suggested_specialty=specialty,
        possible_causes=possible_causes,
        confidence=confidence,
        urgency_band=urgency_band,
        disclaimer=DISCLAIMER,
        model_version=MODEL_VERSION,
        requires_doctor_escalation=requires_doctor_escalation,
    )


def safe_triage_fallback(raw_input: str) -> TriageOutput:
    """
    Called when input fails schema validation or is entirely unparseable.
    Always returns a safe, valid TriageOutput that escalates to doctor.
    Never raises — this is the last-resort safety net.
    """
    return TriageOutput(
        symptoms=[raw_input[:200]] if raw_input else ["unknown"],
        duration="unknown",
        severity="mild",
        red_flags=[],
        concern_level="routine",
        suggested_specialty="General Medicine",
        possible_causes=["Unable to process symptoms. Please consult a doctor directly."],
        confidence=0.0,
        urgency_band="within_week",
        disclaimer=DISCLAIMER,
        model_version=MODEL_VERSION,
        requires_doctor_escalation=True,
    )

