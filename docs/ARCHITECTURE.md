# Architecture

```
Browser (React) ──/api──▶ nginx or Vite proxy ──▶ FastAPI ──▶ PostgreSQL / SQLite
   cookies: access_token (HttpOnly) + csrf_token
```

The frontend and the API are served from the **same origin** (`/api` is proxied). That is why
plain cookies work and no CORS tricks are needed.

## Database schema

```
roles ──┐ parent_id (hierarchy)          permissions
  │     └─▶ roles                           ▲
  │                                         │
  └── role_permissions ─────────────────────┘

locations ─┐
teams ─────┼──▶ users ──▶ auth_logs        (every login attempt)
roles ─────┘      │  └──▶ reset_tokens     (hashed, single use, expiring)
                  │
                  ├──▶ patients            (manager_id = uploader, encrypted fields)
                  └──▶ data_audit          (upload / view / edit / delete)
```

Full SQL: [schema.sql](schema.sql).

| Table | Purpose |
|---|---|
| `roles` | Admin, Manager, User. `parent_id` = role hierarchy (Manager and Admin inherit from User) |
| `permissions`, `role_permissions` | configurable permissions: `profile:view`, `users:manage`, `patients:manage` |
| `locations`, `teams` | US/IN/EU/AU and AR/EPA/PRI as **rows**, not enums |
| `users` | credentials, role/location/team, `is_active`, lockout counters |
| `auth_logs` | audit trail of all logins, success or not |
| `reset_tokens` | password reset (only the SHA-256 of the token is stored) |
| `patients` | `patient_id` plain; name, DOB, gender encrypted; `key_version` per row |
| `data_audit` | who uploaded / viewed / edited / deleted patient data |

## Decisions and why

| Decision | Reason |
|---|---|
| Roles/locations/teams in tables | adding a new one is an INSERT, no code change |
| Permission checks instead of role-name checks | endpoints ask "can this user do `patients:manage`?", so new roles only need new permission rows |
| FastAPI | automatic validation and free Swagger docs |
| JWT in an HttpOnly cookie | JavaScript (and therefore XSS) cannot steal it |
| Vite instead of Next.js | no server-side rendering is needed here, so it is simpler |
| Patient search decrypts in memory | encrypted columns cannot be searched in SQL (see SECURITY.md) |
| Upload is all-or-nothing | clean retry after fixing the file, no half-imported data |
| SQLite fallback | the project runs without Docker or Postgres for quick review |

## Backend layout

- `routers/` only handle HTTP (read input, call logic, return output).
- `validators.py` is shared by the Excel import and the inline edit, so both follow identical rules.
- `crypto.py` is the only file that knows about keys and AES.
- `deps.py` holds the login, permission and CSRF checks.
- `main.py` registers one handler per kind of failure so the frontend always receives `{"detail": "..."}`.

## Adding a new role / location / team

Insert a row (SQL, or the Admin screen for users). Example for a new location:

```sql
INSERT INTO locations (code, name) VALUES ('UK', 'United Kingdom');
```

A new role: insert into `roles`, link permissions in `role_permissions`, optionally set `parent_id`.
