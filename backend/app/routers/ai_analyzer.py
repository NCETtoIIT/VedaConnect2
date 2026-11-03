"""
VedaConnect — AI Analyzer Router (Powered by Google Gemini 3.5 Flash).

Endpoints:
  POST /api/v1/ai/analyze-report  — Parses medical lab report text, identifies normal/abnormal markers,
                                     generates plain language summary and 'Doctor se kya poochhein' questions.
  POST /api/v1/ai/triage-image    — Probabilistic visual assessment (skin rash, superficial wound)
                                     with candidate probabilities and mandatory doctor CTA.
  POST /api/v1/ai/symptom-intake  — Natural multilingual (Hindi/English) symptom extraction.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.services.gemini_service import GeminiAIService

router = APIRouter(prefix="/api/v1/ai", tags=["ai-analyzer"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class ReportAnalysisRequest(BaseModel):
    report_text: str = Field(..., min_length=10, description="Raw text of pathology / lab report")
    language: str = Field("hi", description="Preferred output language: 'hi' (Hindi) or 'en' (English)")


class ImageTriageRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image string")
    mime_type: str = Field("image/jpeg", description="MIME type e.g. image/jpeg, image/png")
    symptoms_text: Optional[str] = Field(None, description="Patient's description of discomfort or duration")


class SymptomIntakeRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Patient free-text or transcribed voice input")
    language: str = Field("en", description="Language of input, e.g. 'hi', 'en', 'hinglish'")


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/analyze-report", summary="AI Medical Report Analyzer & Patient Explanation")
def analyze_report(
    req: ReportAnalysisRequest,
    current_user = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Parses lab reports into patient-friendly explanations with reference ranges
    and 3 specific questions for the doctor ('Doctor se kya poochhein').
    """
    try:
        result = GeminiAIService.analyze_medical_report(
            report_text=req.report_text,
            patient_language=req.language,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report analysis failed: {str(e)}",
        )


@router.post("/triage-image", summary="Probabilistic Visual Triage (Skin / Wound)")
def triage_image(
    req: ImageTriageRequest,
    current_user = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Probabilistic image assessment for skin conditions or superficial wounds.
    Never returns a single definitive disease verdict. Always includes confidence,
    urgency band, and doctor referral CTA.
    """
    try:
        result = GeminiAIService.triage_image_probabilistic(
            image_base64=req.image_base64,
            symptoms_text=req.symptoms_text or "",
            mime_type=req.mime_type,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image triage failed: {str(e)}",
        )


@router.post("/symptom-intake", summary="Multilingual Symptom Intake Extractor")
def symptom_intake(
    req: SymptomIntakeRequest,
) -> Dict[str, Any]:
    """
    Extracts clinical symptoms and urgency from conversational patient text in Hindi or English.
    Deterministic red-flag safety guard runs before and after model inference.
    """
    try:
        result = GeminiAIService.parse_symptom_intake(
            user_input_text=req.text,
            preferred_language=req.language,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Symptom intake failed: {str(e)}",
        )

