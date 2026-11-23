"""
Rules for patient fields.
The same functions are used for Excel rows and for inline edits,
so the data is checked identically wherever it comes from.
Each function returns the cleaned value or raises ValueError with a readable message.
"""
import re
from datetime import date, datetime

from app.config import settings

# letters only (any language), optionally separated by space, apostrophe or hyphen
NAME_PATTERN = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9]{1,30}$")


def validate_patient_id(value) -> str:
    value = str(value or "").strip()
    if not ID_PATTERN.match(value):
        raise ValueError("Patient ID must be letters/numbers only (max 30 characters)")
    # upper-case so "p001" and "P001" count as the same patient
    return value.upper()


def validate_name(value, label: str = "Name") -> str:
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{label} is required")
    if len(value) > 50 or not NAME_PATTERN.match(value):
        raise ValueError(f"{label} may only contain letters, spaces, hyphens or apostrophes (max 50)")
    return value


def validate_dob(value) -> str:
    """Accepts 1990-05-14, 14-05-1990 or 14/05/1990. Returns it as YYYY-MM-DD."""
    text = str(value or "").strip()[:10]  # Excel dates arrive as '1990-05-14 00:00:00'
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            break
        except ValueError:
            continue
    else:
        raise ValueError("Date of Birth is not a valid date (use YYYY-MM-DD)")

    if parsed > date.today() or parsed.year < 1900:
        raise ValueError("Date of Birth must be between 1900 and today")
    return parsed.isoformat()


def validate_gender(value) -> str:
    text = str(value or "").strip().lower()
    for option in settings.GENDER_OPTIONS:
        if option.lower() == text:
            return option
    raise ValueError(f"Gender must be one of: {', '.join(settings.GENDER_OPTIONS)}")
