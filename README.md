# Ncare - Role-Based Login + Encrypted Patient Data

A full-stack take-home project in two parts:

1. **Role-based login** - Admin / Manager / User, with locations (US, IN, EU, AU) and teams (AR, EPA, PRI).
2. **Patient data for Managers** - Excel upload, AES-256 encrypted storage, searchable table with inline editing.

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, axios, plain CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Database | PostgreSQL (Docker) / SQLite (local, zero setup) |
| Security | Argon2 passwords, JWT in HttpOnly cookie, CSRF token, rate limiting, AES-256-GCM |

## Quick start with Docker (one command)

```bash
cp .env.example .env          # then put real keys in it (commands are inside the file)
docker compose up --build
```

Open **http://localhost:3000**. Tables and demo data are created automatically.
API docs (Swagger): http://localhost:8000/api/docs

## Run without Docker

You need Python 3.12+ and Node 20+.

```bash
cp .env.example .env          # fill SECRET_KEY and ENCRYPTION_KEYS

# terminal 1 - backend  (http://localhost:8000)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# terminal 2 - frontend (http://localhost:5173)
cd frontend
npm install
npm run dev
```

## Demo accounts

Password for every account: `Demo@1234`

| Role | Email |
|---|---|
| Admin | admin@ncare.com |
| Manager | manager.us.ar@ncare.com |
| User | user.us.ar@ncare.com |

A manager and a user exist for **every location + team combination**, named
`manager.<location>.<team>@ncare.com` / `user.<location>.<team>@ncare.com`
(e.g. `manager.in.epa@ncare.com`, `user.au.pri@ncare.com`).

## Try it (2 minutes)

1. Log in as **manager.us.ar@ncare.com**.
2. Upload `sample_data/patients_valid.xlsx` (drag & drop). 25 patients appear.
3. Try the files starting with `error_` to see the validation messages.
4. Search, sort, change the page size, click **Edit** on a row, change a name, **Save**.
5. Log in as `manager.in.epa@ncare.com` - the other manager sees none of those patients.
6. Log in as **admin@ncare.com** - add a user, disable one, look at the login activity.

## Project structure

```
ncare/
├── docker-compose.yml     db + backend + frontend
├── .env.example           all configuration keys (copy to .env)
├── backend/
│   ├── app/
│   │   ├── config.py      reads .env, the single place for settings
│   │   ├── logger.py      logs/<date>/info.log and error.log
│   │   ├── models.py      database tables
│   │   ├── security.py    passwords + JWT       crypto.py  AES encryption
│   │   ├── validators.py  field rules           excel_service.py  Excel reading
│   │   ├── deps.py        login / permission / CSRF checks
│   │   ├── routers/       auth.py, users.py, patients.py
│   │   └── seed.py        demo data
│   ├── tests/             25 automated tests
│   ├── rotate_keys.py     re-encrypt data with a new key
│   └── benchmark.py       encryption speed test
├── frontend/src/          pages/ components/ api.js auth.jsx styles.css
├── sample_data/           valid, 10,000-row and error Excel files
└── docs/                  architecture, API, security, user guide, benchmarks, schema.sql
```

## Configuration

Everything is read from `.env` by `backend/app/config.py`. The important ones:

| Variable | Meaning |
|---|---|
| `API_KEY` | key every client must send in the `X-API-Key` header (required) |
| `SECRET_KEY` | signs the login tokens (required) |
| `ENCRYPTION_KEYS` | AES keys as `version:base64`, e.g. `1:abc...` (required) |
| `ACTIVE_KEY_VERSION` | key used for new/updated data |
| `DATABASE_URL` | defaults to SQLite; Docker sets PostgreSQL |
| `MAX_FAILED_ATTEMPTS`, `LOCKOUT_MINUTES` | account lockout rules |
| `LOGIN_RATE_LIMIT` | e.g. `10/minute` per IP |
| `MAX_UPLOAD_MB`, `MAX_UPLOAD_ROWS` | upload limits |

There are no LLM/API keys in this project. `.env` is git-ignored; never commit it.

## Logs

Written to `backend/logs/YYYY-MM-DD/`:
`info.log` (requests, logins, uploads) and `error.log` (errors with full traceback).
With Docker the folder is mounted, so you can read it on your machine.
The password-reset link (there is no mail server) is written to `info.log`.

## Tests

```bash
cd backend && source .venv/bin/activate && pytest -q
```

Covers hashing, validation, encryption (incl. tamper detection), login, lockout, roles,
CSRF, password reset, upload errors, search/sort, inline edit and data isolation.

## Assumptions

- Email is the login name.
- A manager sees only the patients **they uploaded** (other managers of the same team cannot see them).
- Gender options: Male, Female, Other, Prefer not to say (set in `config.py`).
- Dates accepted as `YYYY-MM-DD`, `DD-MM-YYYY` or `DD/MM/YYYY`; stored as `YYYY-MM-DD`.
- An upload is **all-or-nothing**: if any row is invalid nothing is saved, so the manager can
  fix the file and upload it again without creating duplicates.
- A Patient ID that already exists is reported as an error (not overwritten). Edit it in the table instead.
- Admins cannot open patient data. The brief says only Managers can.
- Tables are created automatically on start (`create_all`). `docs/schema.sql` has the SQL for reference.
  For a real production system I would add Alembic migrations.

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ·
[docs/API.md](docs/API.md) · [docs/SECURITY.md](docs/SECURITY.md) ·
[docs/USER_GUIDE.md](docs/USER_GUIDE.md)
