"""
Phase 1: Lead Intake and Missed Contact Recovery.
Deterministic contact matching, spam scoring, phone normalization.
"""

from app.application.intake.phone_utils import normalize_phone, format_display
from app.application.intake.spam import score_call_spam, SpamResult, SpamTier, ALLOW_MAX, QUARANTINE_MAX
from app.application.intake.sms import (
    can_send_sms,
    suppress_phone,
    remove_suppression,
    is_phone_suppressed,
    MISSED_CALL_SMS_MESSAGE,
)

__all__ = [
    "normalize_phone",
    "format_display",
    "score_call_spam",
    "SpamResult",
    "SpamTier",
    "ALLOW_MAX",
    "QUARANTINE_MAX",
    "can_send_sms",
    "suppress_phone",
    "remove_suppression",
    "is_phone_suppressed",
    "MISSED_CALL_SMS_MESSAGE",
]
