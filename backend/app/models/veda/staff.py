"""
VedaConnect — Hospital Staff Model
Maps users to hospitals with designated roles.
"""
import datetime
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from app.database import Base


class HospitalStaffModel(Base):
    """Hospital staff linkage — used for ABAC (hospital-scoped access)."""
    __tablename__ = "hospital_staff"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String, ForeignKey("hospitals.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    designation = Column(String, nullable=False, comment="doctor, admin, nurse, receptionist")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

