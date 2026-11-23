# User guide and test scenarios

## For everyone

- **Sign in** with your email and password. Wrong password 5 times locks the account for 15 minutes.
- **Forgot password?** Use the link on the login page. In this demo the reset link is written to
  `backend/logs/<date>/info.log` (search for `PASSWORD RESET LINK`).
- **Log out** with the button in the top bar. It ends your session.

## User

Your dashboard shows your own details: name, email, role, location, team, status and permissions.

## Manager

1. **Download the template** (Upload section) to see the required format.
2. Required columns, exactly: `Patient ID, First Name, Last Name, Date of Birth, Gender`.
3. **Drag your Excel file** onto the dashed box (or click it). You will see its name and size.
4. Press **Upload file**. A progress bar is shown.
   - Success → "N patients uploaded successfully" and the table refreshes.
   - Problems → a list such as `Row 7: Date of Birth must be between 1900 and today`.
     **Nothing is saved** when any row is wrong. Fix the file and upload again.
5. In the **Patients** table you can search (any field), sort (click a heading), change the page size and move between pages.
6. **Edit** a row: change the fields (changed cells turn yellow), then **Save** or **Cancel**.
   The Patient ID cannot be edited. If saving fails the row goes back to its old values.
7. **Delete** removes a patient after a confirmation.

You only ever see the patients you uploaded yourself.

## Admin

- **Users**: see everyone, **Add user**, **Disable/Enable** an account (enabling also unlocks it).
- **Recent login activity**: the last 20 attempts with result, reason and IP address.

## Test scenarios (sample files are in `sample_data/`)

| # | Scenario | Steps | Expected |
|---|---|---|---|
| 1 | Valid upload | Manager uploads `patients_valid.xlsx` | 25 patients uploaded, table shows them |
| 2 | Large file | Upload `patients_10000.xlsx` (new manager) | 10,000 uploaded in about 1-2 s, table stays responsive |
| 3 | Missing column | `error_missing_column.xlsx` | "Wrong columns - missing columns: Gender" |
| 4 | Invalid values | `error_invalid_values.xlsx` | 5 rows listed with reasons, nothing saved |
| 5 | Duplicate IDs | `error_duplicate_ids.xlsx` | "Patient ID ... appears more than once" |
| 6 | Re-upload same file | Upload `patients_valid.xlsx` twice | second time: "already exists in your records" |
| 7 | Fake Excel | `error_not_excel.xlsx` | "This file is not a valid Excel file" |
| 8 | Wrong type | Choose a `.pdf` or `.csv` | rejected in the browser, and by the server |
| 9 | Data isolation | Log in as `manager.in.epa@ncare.com` | sees none of the other manager's patients |
| 10 | Role guard | Visit `/admin` as a manager | redirected to the manager dashboard |
| 11 | API role guard | User calls `GET /api/patients` | 403 |
| 12 | Lockout | 5 wrong passwords for one account | 6th try: "Account is locked..."; Admin can enable the account |
| 13 | Disabled account | Admin disables a user, user logs in | "Your account is disabled" |
| 14 | Edit validation | Set date of birth in the future, Save | error shown, row restored |
| 15 | Search | Type part of a name, ID or date | matching rows only |
| 16 | Encryption | Open the database (`sqlite3 backend/ncare.db "select * from patients limit 3"`) | names/DOB/gender are unreadable bytes |
| 17 | Password reset | Request reset, take link from `info.log`, set new password | can log in with the new one; link works only once |
| 18 | Key rotation | Add key 2, `ACTIVE_KEY_VERSION=2`, `python rotate_keys.py` | rows re-encrypted, table still readable |

