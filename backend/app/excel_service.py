"""Reads an uploaded Excel file and checks every row before anything touches the database."""
import io

import pandas as pd

from app import validators
from app.config import settings

REQUIRED_COLUMNS = ["Patient ID", "First Name", "Last Name", "Date of Birth", "Gender"]
MAX_ERRORS_SHOWN = 50  # no point sending thousands of messages back

# first bytes of real Excel files: .xlsx is a zip, .xls is the old OLE format
XLSX_MAGIC = b"PK\x03\x04"
XLS_MAGIC = b"\xd0\xcf\x11\xe0"


def read_excel(content: bytes, filename: str) -> pd.DataFrame:
    """Loads the sheet as text. Raises ValueError if it is not a proper Excel file."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ("xlsx", "xls"):
        raise ValueError("Only .xlsx and .xls files are accepted")

    # don't trust the extension alone - check what the file really is
    magic = XLSX_MAGIC if ext == "xlsx" else XLS_MAGIC
    if not content.startswith(magic):
        raise ValueError("This file is not a valid Excel file")

    try:
        df = pd.read_excel(io.BytesIO(content), dtype=str, engine="openpyxl" if ext == "xlsx" else "xlrd")
    except Exception:
        raise ValueError("The Excel file could not be read. Is it damaged?")

    df.columns = [str(c).strip() for c in df.columns]
    return df.fillna("")


def validate_rows(df: pd.DataFrame, existing_ids: set):
    """
    Returns (clean_rows, errors_to_show, total_error_count).
    If there are any errors the whole file is rejected, so the manager can fix it and upload again.
    """
    # 1. the columns must match exactly
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missing columns: {', '.join(missing)}")
        if extra:
            parts.append(f"unexpected columns: {', '.join(extra)}")
        raise ValueError("Wrong columns - " + "; ".join(parts))

    if df.empty:
        raise ValueError("The file has no patient rows")
    if len(df) > settings.MAX_UPLOAD_ROWS:
        raise ValueError(f"Too many rows ({len(df)}). The limit is {settings.MAX_UPLOAD_ROWS}.")

    # 2. check row by row
    rows, errors, seen = [], [], set()
    for index, record in enumerate(df.to_dict("records")):
        excel_row = index + 2  # +1 for the header, +1 because Excel starts at 1
        problems = []
        cleaned = {}

        # each check is tried separately so one row can report several problems at once
        checks = [
            ("patient_id", validators.validate_patient_id, record["Patient ID"]),
            ("first_name", lambda v: validators.validate_name(v, "First Name"), record["First Name"]),
            ("last_name", lambda v: validators.validate_name(v, "Last Name"), record["Last Name"]),
            ("dob", validators.validate_dob, record["Date of Birth"]),
            ("gender", validators.validate_gender, record["Gender"]),
        ]
        for key, check, value in checks:
            try:
                cleaned[key] = check(value)
            except ValueError as e:
                problems.append(str(e))

        # duplicate checks only make sense when the id itself is valid
        if "patient_id" in cleaned:
            pid = cleaned["patient_id"]
            if pid in seen:
                problems.append(f"Patient ID {pid} appears more than once in this file")
            elif pid in existing_ids:
                problems.append(f"Patient ID {pid} already exists in your records")
            seen.add(pid)

        if problems:
            errors.append(f"Row {excel_row}: " + "; ".join(problems))
        else:
            rows.append(cleaned)

    return rows, errors[:MAX_ERRORS_SHOWN], len(errors)


def build_template() -> bytes:
    """A small example file the manager can download and fill in."""
    sample = pd.DataFrame([["P001", "Jane", "Doe", "1990-05-14", "Female"]], columns=REQUIRED_COLUMNS)
    buffer = io.BytesIO()
    sample.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()
