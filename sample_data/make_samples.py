"""
Creates the sample Excel files used for testing.   Run:  python sample_data/make_samples.py
(needs pandas + openpyxl, e.g. use the backend virtual environment)
"""
import random
from pathlib import Path

import pandas as pd

OUT = Path(__file__).parent
COLUMNS = ["Patient ID", "First Name", "Last Name", "Date of Birth", "Gender"]
FIRST = ["Aarav", "Maria", "John", "Priya", "Liam", "Sofia", "Chen", "Fatima", "Oliver", "Emma"]
LAST = ["Sharma", "Garcia", "Smith", "Patel", "Brown", "Rossi", "Wang", "Khan", "O'Brien", "Miller"]
GENDERS = ["Male", "Female", "Other", "Prefer not to say"]

random.seed(7)  # same files every time


def make_rows(count: int, prefix: str):
    rows = []
    for i in range(1, count + 1):
        dob = f"{random.randint(1940, 2015)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        rows.append([f"{prefix}{i:05d}", random.choice(FIRST), random.choice(LAST), dob, random.choice(GENDERS)])
    return rows


def save(name: str, rows, columns=COLUMNS):
    pd.DataFrame(rows, columns=columns).to_excel(OUT / name, index=False)
    print("created", name)


# 1. happy path
save("patients_valid.xlsx", make_rows(25, "P"))

# 2. performance test: the maximum the app accepts
save("patients_10000.xlsx", make_rows(10_000, "B"))

# 3. a column is missing
save("error_missing_column.xlsx", [r[:4] for r in make_rows(3, "M")], COLUMNS[:4])

# 4. bad values: empty name, impossible date, future date, unknown gender, symbols in ID
bad = make_rows(5, "E")
bad[0][1] = ""
bad[1][3] = "31-02-2020"
bad[2][3] = "2999-01-01"
bad[3][4] = "Unknown"
bad[4][0] = "E-5!"
save("error_invalid_values.xlsx", bad)

# 5. the same Patient ID twice in one file
dupes = make_rows(3, "D")
dupes.append(list(dupes[0]))
save("error_duplicate_ids.xlsx", dupes)

# 6. looks like Excel, but is not (wrong format test)
(OUT / "error_not_excel.xlsx").write_text("this is just text pretending to be an excel file")
print("created error_not_excel.xlsx")
