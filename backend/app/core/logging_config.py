"""
VedaConnect Core Logging — Structured JSON logging with PHI scrubber.

The PHI scrubber runs on every log line before it is emitted, redacting:
  - Indian phone numbers (10-digit with optional +91 prefix)
  - Email addresses
  - Aadhaar-like 12-digit numbers
  - Names near PHI keywords (name:, patient_name:, etc.)
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Optional


# ═══════════════════════════════════════════════════════════════
#  PHI Scrubber Patterns
# ═══════════════════════════════════════════════════════════════

_PHI_PATTERNS = [
    # Indian phone numbers: +91-XXXXXXXXXX, +91 XXXXX XXXXX, 10 consecutive digits
    (
        re.compile(
            r"(\+91[\s\-]?)?\b(\d{5}[\s\-]?\d{5})\b"
        ),
        "[PHONE_REDACTED]",
    ),
    # Email addresses
    (
        re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
        ),
        "[EMAIL_REDACTED]",
    ),
    # Aadhaar-like 12-digit numbers (with optional spaces/hyphens)
    (
        re.compile(
            r"\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b"
        ),
        "[AADHAAR_REDACTED]",
    ),
    # Names near PHI keywords
    (
        re.compile(
            r"(?i)((?:patient_?name|full_?name|name|user_?name)\s*[:=]\s*)"
            r"([\"']?)([A-Z][a-z]+(?: [A-Z][a-z]+)*)\2"
        ),
        r"\1[NAME_REDACTED]",
    ),
]


def scrub_phi(text: str) -> str:
    """Remove PHI from a log message string."""
    if not text:
        return text
    result = text
    for pattern, replacement in _PHI_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


# ═══════════════════════════════════════════════════════════════
#  JSON Log Formatter
# ═══════════════════════════════════════════════════════════════

class PHIScrubberJSONFormatter(logging.Formatter):
    """
    Structured JSON log formatter with PHI scrubbing.
    Every log line is emitted as a single JSON object.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Scrub the message
        raw_message = record.getMessage()
        scrubbed_message = scrub_phi(raw_message)

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": scrubbed_message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            exc_text = self.formatException(record.exc_info)
            log_entry["exception"] = scrub_phi(exc_text)

        # Include extra fields (if any were added via logger.info("msg", extra={...}))
        for key in ("request_id", "user_id", "action", "resource"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = scrub_phi(str(val)) if isinstance(val, str) else val

        return json.dumps(log_entry, default=str)


# ═══════════════════════════════════════════════════════════════
#  Setup Function
# ═══════════════════════════════════════════════════════════════

def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure structured JSON logging with PHI scrubbing for the
    entire application.

    Call this once at startup (e.g., in main.py).
    """
    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)

    # Create the PHI-scrubbing JSON handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PHIScrubberJSONFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate output
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress noisy third-party loggers
    for noisy_logger in ("uvicorn.access", "sqlalchemy.engine", "httpcore"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # Set our application logger
    app_logger = logging.getLogger("vedaconnect")
    app_logger.setLevel(log_level)
    app_logger.info("VedaConnect structured JSON logging initialized (PHI scrubber active)")
