"""
VedaConnect New Models — extends CHIKITSA-X data model per architecture.md §4.
All additive — existing models are NOT modified.
"""
from app.models.veda.consent import VedaConsentModel
from app.models.veda.audit import VedaAuditLogModel
from app.models.veda.booking import VedaBookingModel, JourneyEventModel
from app.models.veda.attachments import AttachmentModel, ReportExtractionModel, ImageAssessmentModel
from app.models.veda.blood import BloodBankModel, BloodStockModel, DonorModel, BloodRequestModel
from app.models.veda.reminders import ReminderModel, ReminderLogModel, ConsultModel, FeedbackModel
from app.models.veda.beds import BedModel, AvailabilitySignalModel
from app.models.veda.staff import HospitalStaffModel

__all__ = [
    "VedaConsentModel",
    "VedaAuditLogModel",
    "VedaBookingModel",
    "JourneyEventModel",
    "AttachmentModel",
    "ReportExtractionModel",
    "ImageAssessmentModel",
    "BloodBankModel",
    "BloodStockModel",
    "DonorModel",
    "BloodRequestModel",
    "ReminderModel",
    "ReminderLogModel",
    "ConsultModel",
    "FeedbackModel",
    "BedModel",
    "AvailabilitySignalModel",
    "HospitalStaffModel",
]
