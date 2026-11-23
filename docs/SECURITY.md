# Security and encryption

## What is protected and how

| Threat | Protection |
|---|---|
| Unknown callers hitting the API | every `/api` call needs the `X-API-Key` header (constant-time comparison, key kept in `.env`) |
| Stolen password database | Argon2id hashes with automatic random salt |
| Weak passwords | min 8 chars + upper, lower, number, symbol |
| Brute force | account locks 15 min after 5 failures + per-IP rate limit on login/reset |
| Finding out which emails exist | same error for "wrong password" and "unknown email"; reset always answers the same |
| Token theft via XSS | JWT lives in an **HttpOnly** cookie, JavaScript cannot read it |
| CSRF | double-submit token: cookie value must match the `X-CSRF-Token` header on every change |
| SQL injection | SQLAlchemy parameterised queries only; search runs in memory, sort field is checked against a whitelist |
| XSS | React escapes all output; names are limited to letters/space/hyphen/apostrophe, so `=cmd()` or `<script>` are rejected (also blocks Excel formula injection) |
| Fake Excel files | extension **and** file signature are checked, size and row limits applied |
| Reading another manager's patients | every query filters by `manager_id`; other managers get 404 |
| Privilege abuse | endpoints require a permission; Admin cannot open patient data |
| Reset token leak | only its SHA-256 is stored; single use; expires in 30 min |
| Clickjacking / sniffing | `X-Frame-Options`, `X-Content-Type-Options` headers |
| Error leaks | unexpected errors return a generic message; the traceback goes only to `error.log` |

All sessions end on logout (cookies removed) or after `TOKEN_EXPIRE_MINUTES`.

## Encryption (AES-256-GCM)

Encrypted in the application **before** reaching the database: first name, last name, date of birth, gender.

- **Random nonce per value**: the same name encrypted twice looks different in the database.
- **Authenticated**: GCM detects any change to the stored bytes.
- **Bound to its place**: the field name + patient ID are part of the "associated data", so copying a
  ciphertext to another patient/column makes decryption fail (tested in `test_units.py`).
- Stored as `nonce(12 bytes) + ciphertext + tag` in a binary column, together with `key_version`.

### Why Patient ID is NOT encrypted

It is an opaque identifier chosen by the organisation (not a name, SSN or medical record number).
Keeping it readable allows a unique constraint per manager, duplicate detection on upload,
and fast lookups with a normal index. If it were a real-world identifier it should be encrypted too,
with a keyed-hash (HMAC) "blind index" for lookups.

### Searching encrypted data

SQL cannot search or sort inside ciphertext. So the API decrypts **only the logged-in manager's rows**
in memory and filters/sorts there. Measured cost for 10,000 patients,
Trade-off: it is O(n) per request. For millions of rows the next step would be blind indexes
for exact matches, plus pagination in SQL.

### Key management and rotation

- Keys live in `.env` (`ENCRYPTION_KEYS=1:...,2:...`), never in the code or the database.
- Every row stores the `key_version` it was encrypted with, so several keys can exist at once.
- Rotate: add key `2` → set `ACTIVE_KEY_VERSION=2` → run `python rotate_keys.py` (re-encrypts in batches
  of 500) → when it reports nothing left on key 1, remove it.
- In production the keys should come from a secrets manager / KMS (AWS KMS, Vault) instead of a file.
  The code only needs `settings.ENCRYPTION_KEYS`, so that swap is limited to `config.py`.

### Audit trail

- `data_audit` table: every upload, table load (view), edit and delete, with user and time.
  Table loads are logged once per request ("N records decrypted"), not once per field,
  to keep the table small.
- `auth_logs` table: every login attempt. `logs/<date>/info.log`: all requests and events.

## Known limitations (honest list)

- The API key is built into the React bundle, so anyone who opens the browser dev tools can read it.
  It only keeps out callers who do not know it (scripts, other apps); it is **not** a user secret.
  Real access control is the login + roles. For a stricter setup, let nginx add the header
  (`proxy_set_header X-API-Key ...`) so it never reaches the browser.
- No email server: the reset link is printed to `info.log`.
- The JWT cannot be revoked before it expires (logout only removes the cookie). A refresh-token
  table would fix that.
- Set `COOKIE_SECURE=true` and serve over HTTPS in a real deployment.
- Rate limiting is in memory (per process); use Redis if you run several backend processes.
- HIPAA needs more than code (TLS, access reviews, backups, BAAs). This project covers the application-level parts.
