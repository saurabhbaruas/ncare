"""
Re-encrypts every patient row with the currently active key.

How to rotate:
  1. add a new key to ENCRYPTION_KEYS in .env      e.g.  1:oldkey,2:newkey
  2. set ACTIVE_KEY_VERSION=2
  3. run:  python rotate_keys.py
  4. once it reports 0 rows left on old keys, the old key can be retired.
"""
from app.config import settings
from app.crypto import decrypt_patient, encrypt_patient
from app.database import SessionLocal
from app.logger import logger
from app.models import Patient

BATCH = 500


def rotate():
    done = 0
    with SessionLocal() as db:
        while True:
            # always fetch the next batch that is still on an old key
            rows = (db.query(Patient)
                    .filter(Patient.key_version != settings.ACTIVE_KEY_VERSION)
                    .limit(BATCH).all())
            if not rows:
                break
            try:
                for row in rows:
                    plain = decrypt_patient(row)
                    for column, value in encrypt_patient(row.patient_id, plain).items():
                        setattr(row, column, value)
                db.commit()
            except Exception:
                # keep whatever earlier batches finished, report the problem
                db.rollback()
                logger.exception("Key rotation stopped because of an error")
                raise
            done += len(rows)
            print(f"re-encrypted {done} rows...")

    logger.info(f"Key rotation finished: {done} rows now use key v{settings.ACTIVE_KEY_VERSION}")
    print(f"Done. {done} rows rotated to key v{settings.ACTIVE_KEY_VERSION}.")


if __name__ == "__main__":
    rotate()
