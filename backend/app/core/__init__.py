"""
VedaConnect Core Infrastructure & Security Module
"""
from app.core.config import settings
from app.core.security import (
    hash_password_argon2,
    verify_password_argon2,
    verify_password_universal,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    verify_refresh_token_family,
    get_current_user,
    get_current_user_optional,
)
from app.core.rbac import require_role, require_hospital_scope
from app.core.audit import log_audit
from app.core.errors import setup_exception_handlers
from app.core.logging_config import setup_logging, scrub_phi

__all__ = [
    "settings",
    "hash_password_argon2",
    "verify_password_argon2",
    "verify_password_universal",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
    "verify_refresh_token_family",
    "get_current_user",
    "get_current_user_optional",
    "require_role",
    "require_hospital_scope",
    "log_audit",
    "setup_exception_handlers",
    "setup_logging",
    "scrub_phi",
]
