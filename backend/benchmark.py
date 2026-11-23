"""
Measures how much the encryption costs.   Run:  python benchmark.py
Uses fake patients in memory only - the real database is not touched.
"""
import time
from types import SimpleNamespace

from app.crypto import decrypt_patient, encrypt_patient

COUNTS = [1_000, 10_000]


def run(count: int):
    plain = {"first_name": "Jane", "last_name": "Doe", "dob": "1990-05-14", "gender": "Female"}

    # encrypt `count` patients (4 fields each)
    start = time.perf_counter()
    encrypted = [encrypt_patient(f"P{i}", plain) for i in range(count)]
    enc_time = time.perf_counter() - start

    # build row-like objects and decrypt them again
    rows = [SimpleNamespace(patient_id=f"P{i}", **data) for i, data in enumerate(encrypted)]
    start = time.perf_counter()
    for row in rows:
        decrypt_patient(row)
    dec_time = time.perf_counter() - start

    print(f"{count:>7,} patients | encrypt {enc_time * 1000:8.1f} ms | decrypt {dec_time * 1000:8.1f} ms "
          f"| {dec_time / count * 1000:.3f} ms per patient")


if __name__ == "__main__":
    for n in COUNTS:
        run(n)
