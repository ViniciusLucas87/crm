"""
Phone number normalization and validation utilities.
E.164 formatting for Canadian numbers. Cached for performance.
"""

import re
from functools import lru_cache

# Canadian area codes (partial reference list for validation)
_CANADIAN_AREA_CODES = frozenset({
    "204", "226", "236", "249", "250", "263", "289", "306", "343",
    "354", "365", "367", "368", "403", "416", "418", "428", "431",
    "437", "438", "450", "468", "474", "506", "514", "519", "548",
    "579", "581", "584", "587", "604", "613", "639", "647", "672",
    "683", "705", "709", "742", "753", "778", "780", "782", "807",
    "819", "825", "867", "873", "879", "902", "905",
})

_VOIP_PREFIXES = frozenset({"500", "533", "544", "566", "577", "588"})

@lru_cache(maxsize=2048)
def normalize_phone(raw: str | None) -> str | None:
    """Normalize to E.164: +1XXXXXXXXXX for Canadian/US numbers.
    Returns None for unparseable input.
    """
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if len(digits) >= 10 and len(digits) <= 15:
        return f"+{digits}"
    return None


def is_canadian(number: str | None) -> bool:
    """Check if normalized number appears to be Canadian."""
    if not number:
        return False
    n = number if number.startswith("+") else f"+{number}"
    if not n.startswith("+1"):
        return False
    if len(n) != 12:
        return False
    area = n[2:5]
    return area in _CANADIAN_AREA_CODES


def is_voip_or_toll_free(number: str) -> bool:
    """Check if number is VoIP range or toll-free."""
    digits = re.sub(r"\D", "", number)
    if len(digits) >= 3:
        area = digits[-10:-7] if len(digits) > 10 else digits[:3]
        if area in _VOIP_PREFIXES or area in ("800", "833", "844", "855", "866", "877", "888"):
            return True
    return False


def format_display(phone: str | None) -> str:
    """Display-friendly: (604) 555-0123"""
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone
