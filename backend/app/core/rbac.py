"""
VedaConnect Core RBAC — Role-Based & Attribute-Based Access Control.

Roles: patient, caregiver, doctor, hospital_admin, super_admin
Case-insensitive matching for backward compatibility with existing
uppercase roles (PATIENT, DOCTOR, HOSPITAL_ADMIN, etc.).
"""

from typing import List

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, get_db
from app.models.user import UserModel


# ── Canonical Role Constants ─────────────────────────────────────
ROLE_PATIENT = "patient"
ROLE_CAREGIVER = "caregiver"
ROLE_DOCTOR = "doctor"
ROLE_HOSPITAL_ADMIN = "hospital_admin"
ROLE_SUPER_ADMIN = "super_admin"

ALL_ROLES = {
    ROLE_PATIENT,
    ROLE_CAREGIVER,
    ROLE_DOCTOR,
    ROLE_HOSPITAL_ADMIN,
    ROLE_SUPER_ADMIN,
}

# Legacy role aliases from existing CHIKITSA-X data
_ROLE_ALIASES = {
    "PATIENT": ROLE_PATIENT,
    "CAREGIVER": ROLE_CAREGIVER,
    "DOCTOR": ROLE_DOCTOR,
    "HOSPITAL_ADMIN": ROLE_HOSPITAL_ADMIN,
    "HOSPITAL_STAFF": ROLE_HOSPITAL_ADMIN,  # treat staff as admin for RBAC
    "ADMIN": ROLE_SUPER_ADMIN,
    "SUPER_ADMIN": ROLE_SUPER_ADMIN,
}


def normalize_role(role: str) -> str:
    """Normalize a role string to canonical lowercase form."""
    if not role:
        return ROLE_PATIENT
    upper = role.strip().upper()
    return _ROLE_ALIASES.get(upper, role.strip().lower())


# ═══════════════════════════════════════════════════════════════
#  RBAC Dependency Factory
# ═══════════════════════════════════════════════════════════════

def require_role(allowed_roles: List[str]):
    """
    FastAPI dependency factory ensuring the current user has one of
    the required roles.

    Usage:
        @router.get("/admin-only")
        def admin_endpoint(user = Depends(require_role(["super_admin", "hospital_admin"]))):
            ...

    Accepts both canonical ("doctor") and legacy ("DOCTOR") role names.
    """
    # Normalize the allowed list at dependency creation time
    normalized_allowed = {normalize_role(r) for r in allowed_roles}

    def role_checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        user_role_normalized = normalize_role(user.role)
        if user_role_normalized not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role in {sorted(normalized_allowed)}, "
                    f"your role is '{user.role}'."
                ),
            )
        return user

    return role_checker


# ═══════════════════════════════════════════════════════════════
#  ABAC — Hospital Scope Check
# ═══════════════════════════════════════════════════════════════

def require_hospital_scope(hospital_id_param: str = "hospital_id"):
    """
    ABAC dependency: hospital staff can only access rows
    where hospital_id matches their own hospital.

    The `hospital_id_param` is the name of the path/query parameter
    that carries the target hospital_id in the request.

    Super-admins bypass the hospital scope check.

    Usage:
        @router.get("/hospitals/{hospital_id}/patients")
        def list_patients(
            hospital_id: str,
            user = Depends(require_hospital_scope("hospital_id")),
        ):
            ...
    """

    def scope_checker(
        user: UserModel = Depends(get_current_user),
        db: Session = Depends(get_db),
        **kwargs,
    ) -> UserModel:
        user_role = normalize_role(user.role)

        # Super-admins have cross-hospital access
        if user_role == ROLE_SUPER_ADMIN:
            return user

        # Patients access their own data via other mechanisms (not hospital-scoped)
        if user_role == ROLE_PATIENT:
            return user

        # Hospital staff must have a hospital_id assigned
        if not user.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not associated with any hospital.",
            )

        return user

    return scope_checker


def check_hospital_match(user: UserModel, target_hospital_id: str) -> None:
    """
    Explicit check that a user's hospital matches the target.
    Raises 403 if mismatch. Super-admins are exempt.
    """
    user_role = normalize_role(user.role)
    if user_role == ROLE_SUPER_ADMIN:
        return
    if user.hospital_id != target_hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied. Your hospital ({user.hospital_id}) does not match "
                f"the target resource's hospital ({target_hospital_id})."
            ),
        )
