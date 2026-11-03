"""
VedaConnect — Google Gemini AI Integration Service.

Provides:
  1. Medical Report Analyzer (extracts test parameters, explains values in simple language,
     flags abnormalities, generates 'Doctor se kya poochhein' questions).
  2. Probabilistic Image Triage (evaluates rash/lesion/wound images with candidate probabilities,
     strict non-diagnostic guardrails, confidence score, urgency band).
  3. AI Symptom Intake & Understanding (multilingual Hindi/English symptom extraction).

Compliance & Safety (rules.md & architecture.md):
  - Temperature <= 0.2 for clinical determinism
  - Deterministic red-flag safety guard always runs first
  - NEVER provides definitive disease diagnoses (strictly probabilistic candidate causes)
  - Mandatory clinical & legal disclaimers on every response
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.services.veda_triage_service import _check_red_flags, DISCLAIMER, MODEL_VERSION

logger = logging.getLogger("vedaconnect.ai")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


FALLBACK_MODELS = [
    "models/gemini-3.5-flash",
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.1-flash-lite",
]


def _call_gemini_raw(
    prompt: str,
    system_instruction: Optional[str] = None,
    image_base64: Optional[str] = None,
    mime_type: str = "image/jpeg",
    temperature: float = 0.2,
) -> str:
    """Call Google Gemini REST API using httpx with resilience and model fallbacks."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in backend environment.")

    configured_model = settings.GEMINI_MODEL or "gemini-3.5-flash"
    if not configured_model.startswith("models/"):
        configured_model = f"models/{configured_model}"

    models_to_try = [configured_model] + [m for m in FALLBACK_MODELS if m != configured_model]

    parts: List[Dict[str, Any]] = []

    if image_base64:
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": image_base64
            }
        })

    parts.append({"text": prompt})

    contents = [{"parts": parts}]

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 4096,
            "responseMimeType": "application/json",
        }
    }

    if system_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    last_error: Optional[Exception] = None

    with httpx.Client(timeout=45.0) as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
            try:
                response = client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    res_data = response.json()
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return text_content
                logger.warning("Gemini model %s returned status %d: %s. Trying fallback...", model, response.status_code, response.text[:200])
                last_error = RuntimeError(f"{model} failed: {response.status_code} - {response.text[:200]}")
            except Exception as e:
                logger.warning("Gemini model %s request exception: %s. Trying fallback...", model, str(e))
                last_error = e

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def _extract_json_from_llm(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code fences and extract valid JSON."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback regex search for { ... }
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


class GeminiAIService:
    """Enterprise clinical AI service for VedaConnect."""

    @staticmethod
    def analyze_medical_report(
        report_text: str,
        patient_language: str = "hi",  # hi or en
    ) -> Dict[str, Any]:
        """
        Analyze pathology or lab report text.
        Extracts parameters, simplifies findings, identifies abnormal values,
        and provides doctor consultation guidance.
        """
        system_prompt = (
            "You are VedaConnect's clinical report comprehension assistant. "
            "Your role is to translate complex laboratory and pathology reports into simple, calm, "
            "informative summaries for patients in India. "
            "RULES: "
            "1. NEVER give a definitive disease diagnosis. "
            "2. Explain tests in simple terms (e.g. Hemoglobin = red blood cells carrying oxygen). "
            "3. Identify normal vs out-of-range values with standard clinical reference bounds. "
            "4. Provide 3 specific, constructive questions for the patient to ask their doctor ('Doctor se kya poochhein'). "
            "5. Respond in valid JSON only with keys: "
            "summary, parameters (array of {name, value, unit, reference_range, status: 'NORMAL'|'HIGH'|'LOW', explanation}), "
            "abnormal_highlights (array of str), doctor_questions (array of 3 str), urgency: 'ROUTINE'|'PROMPT'|'EMERGENCY'."
        )

        user_prompt = f"""
Language requested for patient: {patient_language}
Report Content to analyze:
{report_text}

Output JSON only:
"""
        raw_resp = _call_gemini_raw(prompt=user_prompt, system_instruction=system_prompt, temperature=0.1)
        data = _extract_json_from_llm(raw_resp)

        data["disclaimer"] = DISCLAIMER
        data["model_version"] = f"gemini-report-{MODEL_VERSION}"
        data["requires_doctor_consult"] = True
        return data

    @staticmethod
    def triage_image_probabilistic(
        image_base64: str,
        symptoms_text: str = "",
        mime_type: str = "image/jpeg",
    ) -> Dict[str, Any]:
        """
        Probabilistic image triage (rash, skin lesion, superficial wound).
        Per rules.md: NEVER give a definitive diagnosis.
        Returns candidate causes with probabilities, confidence score, urgency band,
        and immediate red-flag emergency detection.
        """
        # Step 1: Pre-call red flag check on patient symptom text
        triggered_red_flags = _check_red_flags(symptoms_text) if symptoms_text else []

        system_prompt = (
            "You are a clinical decision support system for superficial image assessment (dermatology/wound triage). "
            "CRITICAL CLINICAL & LEGAL INVARIANTS: "
            "1. NEVER diagnose the exact disease. "
            "2. Return candidate possibilities as a probabilistic distribution (percentages summing to 100). "
            "3. Provide confidence between 0.0 and 1.0. If image quality is poor or ambiguous, set confidence < 0.5. "
            "4. Assign urgency band: 'now' (emergency), 'within_24h' (urgent OPD), or 'within_week' (routine). "
            "5. Give clear visual observations (e.g., erythematous patch with scaling). "
            "6. Output JSON only with keys: "
            "visual_observations (str), candidate_possibilities (array of {condition: str, probability_percentage: int, explanation: str}), "
            "confidence: float, urgency_band: str, suggested_specialty: str, home_care_precautions: array of str, "
            "warning_signs_to_watch: array of str."
        )

        user_prompt = f"""
Additional patient description: {symptoms_text or 'None provided'}
Analyze the attached image and provide clinical triage decision support. Output JSON only.
"""

        raw_resp = _call_gemini_raw(
            prompt=user_prompt,
            system_instruction=system_prompt,
            image_base64=image_base64,
            mime_type=mime_type,
            temperature=0.15,
        )

        data = _extract_json_from_llm(raw_resp)

        # If red-flags were detected or urgency is 'now', force emergency CTA
        if triggered_red_flags or data.get("urgency_band") == "now":
            data["urgency_band"] = "now"
            data["concern_level"] = "emergency"
            data["emergency_triggered"] = True
        else:
            data["concern_level"] = "urgent" if data.get("urgency_band") == "within_24h" else "routine"
            data["emergency_triggered"] = False

        data["disclaimer"] = (
            "Visual assessment support only. Images can be deceiving and do NOT replace an in-person physical examination. "
            "Always consult a registered medical practitioner."
        )
        data["model_version"] = f"gemini-vision-{MODEL_VERSION}"
        data["requires_doctor_escalation"] = True
        return data

    @staticmethod
    def parse_symptom_intake(
        user_input_text: str,
        preferred_language: str = "en",
    ) -> Dict[str, Any]:
        """
        Extract symptoms, timeline, and severity from natural patient speech or text
        in Indic languages (Hindi, Hinglish, English).
        """
        # Step 1: Deterministic red-flag check ALWAYS runs first
        red_flags = _check_red_flags(user_input_text)

        system_prompt = (
            "You are an empathetic medical intake assistant. "
            "Extract clinical intake parameters from patient statements in English or Indic languages/Hinglish. "
            "Output JSON with keys: "
            "symptoms: array of str, duration: str, severity: 'mild'|'moderate'|'severe', "
            "suggested_specialty: str, patient_summary_en: str, patient_summary_local: str."
        )

        raw_resp = _call_gemini_raw(
            prompt=f"Patient input ({preferred_language}):\n{user_input_text}\nOutput JSON only.",
            system_instruction=system_prompt,
            temperature=0.1,
        )
        parsed = _extract_json_from_llm(raw_resp)

        # Overwrite red flags with deterministic ground truth
        parsed["red_flags"] = red_flags
        if red_flags:
            parsed["concern_level"] = "emergency"
            parsed["urgency_band"] = "now"
        else:
            parsed["concern_level"] = "urgent" if parsed.get("severity") in ["severe", "moderate"] else "routine"
            parsed["urgency_band"] = "within_24h" if parsed["concern_level"] == "urgent" else "within_week"

        parsed["disclaimer"] = DISCLAIMER
        parsed["model_version"] = f"gemini-intake-{MODEL_VERSION}"
        return parsed
