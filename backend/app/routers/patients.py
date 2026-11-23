"""
Patient data (Managers only).
A manager can only ever see and change the patients they uploaded themselves.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app import excel_service
from app.config import settings
from app.crypto import decrypt_patient, encrypt_patient
from app.database import get_db
from app.deps import require_permission
from app.logger import logger
from app.models import DataAudit, Patient, User
from app.schemas import PatientUpdateIn

router = APIRouter(prefix="/patients", tags=["patients"])
manager_only = require_permission("patients:manage")

SORTABLE = ["patient_id", "first_name", "last_name", "dob", "gender"]


def audit(db: Session, user: User, action: str, patient_id: str = None, detail: str = ""):
    """Writes one row to the data audit table. The caller commits."""
    db.add(DataAudit(user_id=user.id, action=action, patient_id=patient_id, detail=detail))


def to_dict(row: Patient) -> dict:
    """Decrypts a row so it can be shown in the table."""
    return {"id": row.id, "patient_id": row.patient_id, **decrypt_patient(row)}


def get_own_patient(db: Session, user: User, pk: int) -> Patient:
    """Finds a patient, but only if it belongs to this manager (otherwise 404)."""
    row = db.query(Patient).filter(Patient.id == pk, Patient.manager_id == user.id).first()
    if not row:
        raise HTTPException(404, "Patient not found")
    return row


@router.get("/template")
def download_template(_user: User = Depends(manager_only)):
    return Response(
        excel_service.build_template(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="patient_template.xlsx"'},
    )


@router.post("/upload")
async def upload_patients(file: UploadFile, db: Session = Depends(get_db),
                          user: User = Depends(manager_only)):
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    # read one byte more than allowed, so we know when the file is too big
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(413, f"File is too large (limit {settings.MAX_UPLOAD_MB} MB)")

    try:
        df = excel_service.read_excel(content, file.filename or "")
        existing = {pid for (pid,) in db.query(Patient.patient_id).filter(Patient.manager_id == user.id)}
        rows, errors, error_count = excel_service.validate_rows(df, existing)
    except ValueError as e:
        # problems with the file as a whole (wrong type, wrong columns, empty...)
        raise HTTPException(400, str(e))
    except Exception:
        logger.exception("Unexpected error while reading the upload")
        raise HTTPException(500, "Could not process the file")

    # any bad row -> nothing is saved, the manager fixes the file and tries again
    if errors:
        raise HTTPException(422, {
            "message": f"{error_count} row(s) have problems. Nothing was saved.",
            "errors": errors,
        })

    try:
        # encrypt every field before it goes near the database
        for r in rows:
            pid = r["patient_id"]
            db.add(Patient(patient_id=pid, manager_id=user.id, **encrypt_patient(pid, r)))
        audit(db, user, "upload", detail=f"{len(rows)} patients from {file.filename}")
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Saving uploaded patients failed")
        raise HTTPException(500, "Could not save the patients, please try again")

    logger.info(f"UPLOAD {len(rows)} patients by {user.email}")
    return {"processed": len(rows), "message": f"{len(rows)} patients uploaded successfully"}


@router.get("")
def list_patients(page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=1000),
                  q: str = "", sort: str = "patient_id", order: str = "asc",
                  db: Session = Depends(get_db), user: User = Depends(manager_only)):
    if sort not in SORTABLE or order not in ("asc", "desc"):
        raise HTTPException(400, "Invalid sort option")

    try:
        # Names, dates and gender are encrypted in the DB, so SQL cannot search or sort them.
        # We decrypt this manager's rows in memory instead (fast enough for 10,000 rows,
        # see docs/BENCHMARKS.md).
        rows = db.query(Patient).filter(Patient.manager_id == user.id).all()
        data = [to_dict(r) for r in rows]
    except Exception:
        logger.exception("Could not load patients")
        raise HTTPException(500, "Could not load patients")

    # search across every field
    if q.strip():
        needle = q.strip().lower()
        data = [d for d in data if any(needle in str(d[f]).lower() for f in SORTABLE)]

    data.sort(key=lambda d: str(d[sort]).lower(), reverse=(order == "desc"))
    total = len(data)
    start = (page - 1) * size

    # one audit row per request, not per field
    audit(db, user, "view", detail=f"{len(rows)} records decrypted for the table")
    db.commit()
    return {"items": data[start:start + size], "total": total, "page": page, "size": size}


@router.patch("/{pk}")
def update_patient(pk: int, body: PatientUpdateIn, db: Session = Depends(get_db),
                   user: User = Depends(manager_only)):
    row = get_own_patient(db, user, pk)
    changes = body.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(400, "Nothing to update")

    try:
        # decrypt -> apply changes -> encrypt again (with the current key)
        current = decrypt_patient(row)
        current.update(changes)
        for column, value in encrypt_patient(row.patient_id, current).items():
            setattr(row, column, value)
        audit(db, user, "edit", row.patient_id, f"fields: {', '.join(changes)}")
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(f"Updating patient {pk} failed")
        raise HTTPException(500, "Could not update the patient")

    return to_dict(row)


@router.delete("/{pk}")
def delete_patient(pk: int, db: Session = Depends(get_db), user: User = Depends(manager_only)):
    row = get_own_patient(db, user, pk)
    try:
        audit(db, user, "delete", row.patient_id)
        db.delete(row)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(f"Deleting patient {pk} failed")
        raise HTTPException(500, "Could not delete the patient")
    return {"message": "Patient deleted"}
