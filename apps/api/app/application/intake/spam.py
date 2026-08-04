"""
Deterministic spam scoring for inbound contacts and calls.
No AI. Pure rules. Transparent reasons.

SpamTier:
  ALLOW     0-29  -- safe, can auto-SMS
  QUARANTINE 30-59 -- uncertain, no auto-SMS, but still record
  BLOCK      60-100 -- rejected, no SMS, no auto-recovery
"""

import re
from enum import Enum


class SpamTier(str, Enum):
    ALLOW = "allow"
    QUARANTINE = "quarantine"
    BLOCK = "block"


ALLOW_MAX = 29
QUARANTINE_MAX = 59


class SpamResult:
    def __init__(self, score: int = 0, reasons: list[str] | None = None):
        self.score = min(max(score, 0), 100)
        self.reasons: list[str] = reasons or []
        self.tier = SpamTier.ALLOW if self.score <= ALLOW_MAX else (
            SpamTier.QUARANTINE if self.score <= QUARANTINE_MAX else SpamTier.BLOCK
        )

    @property
    def quarantine(self) -> bool:
        return self.tier in (SpamTier.QUARANTINE, SpamTier.BLOCK)

    def can_send_sms(self) -> bool:
        return self.tier == SpamTier.ALLOW


def score_call_spam(
    caller_number: str | None = None,
    duration_seconds: int = 0,
    call_status: str = "",
    disconnect_reason: str = "",
) -> SpamResult:
    """Score an inbound call for spam indicators. Deterministic rules only."""
    reasons: list[str] = []
    score = 0

    # 1. Very short ring + immediate hangup (robocall probe)
    if duration_seconds == 0 and call_status in ("MISSED", "COMPLETED"):
        score += 20
        reasons.append("zero_duration_hangup")

    # 2. Extremely short answered call with no meaningful conversation
    if duration_seconds > 0 and duration_seconds < 3 and call_status == "COMPLETED":
        score += 30
        reasons.append("sub_3sec_answered")

    # 3. VoIP or toll-free caller (weaker signal: common but not always spam)
    if caller_number and _is_voip_or_toll_free(caller_number):
        score += 8
        reasons.append("voip_or_toll_free")

    # 4. Caller ID missing or too short
    if not caller_number or len(re.sub(r"\D", "", caller_number)) < 10:
        score += 25
        reasons.append("invalid_caller_id")

    # 5. Suspicious disconnect pattern
    if disconnect_reason and "reject" in disconnect_reason.lower():
        score += 10
        reasons.append("rejected_disconnect")

    return SpamResult(score=min(score, 100), reasons=reasons)


def _is_voip_or_toll_free(number: str) -> bool:
    """Check if a number is in a toll-free or VoIP range.
    North American toll-free codes: 800, 833, 844, 855, 866, 877, 888.
    VoIP ranges are harder to detect; this is a best-effort heuristic.
    """
    digits = re.sub(r"\D", "", number)
    toll_free_codes = {"800", "833", "844", "855", "866", "877", "888"}
    if len(digits) >= 10 and digits[-10:-7] in toll_free_codes:
        return True
    return False
