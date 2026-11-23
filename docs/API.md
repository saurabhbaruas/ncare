# API

Interactive docs (try it in the browser): **http://localhost:8000/api/docs**

All paths start with `/api`. Two layers protect them:

1. **API key** - every call must send the header `X-API-Key: <API_KEY from .env>`.
   Missing or wrong → `403 Invalid or missing API key`. Only `GET /api/health` is open.
2. **Login** - a cookie set by the login call (user-level access, roles, permissions).

Example with curl:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "X-API-Key: <your key>" -H "Content-Type: application/json" \
  -d '{"email":"admin@ncare.com","password":"Demo@1234"}'
```
In Swagger (`/api/docs`) click **Authorize**, paste the key once, and every "Try it out" call includes it.
The React app sends the key automatically (`frontend/src/api.js`).

Every request that changes data (POST/PATCH/DELETE) must send the `X-CSRF-Token` header
(the frontend does this automatically).

Errors always look like `{"detail": "readable message"}`
(upload row errors: `{"detail": {"message": "...", "errors": ["Row 2: ..."]}}`).

## Auth

| Method | Path | Access | Notes |
|---|---|---|---|
| POST | `/auth/login` | public, rate limited | `{email, password}` → user details + cookies. 401 bad credentials, 403 disabled, 423 locked, 429 too many requests |
| POST | `/auth/logout` | public | clears the cookies |
| GET | `/auth/me` | logged in | current user |
| POST | `/auth/password-reset/request` | public, rate limited | `{email}`, always the same answer |
| POST | `/auth/password-reset/confirm` | public | `{token, new_password}` |

## Users (Admin only, except /meta)

| Method | Path | Notes |
|---|---|---|
| GET | `/meta` | any logged-in user. Roles, locations, teams, genders for dropdowns |
| GET | `/users` | all users |
| POST | `/users` | `{email, full_name, password, role_id, location_id, team_id}` → 201, 409 if email exists |
| PATCH | `/users/{id}/status` | `{is_active}`. Enabling also clears a lockout. You cannot disable yourself |
| GET | `/activity` | last 20 login attempts |

## Patients (Manager only, own uploads only)

| Method | Path | Notes |
|---|---|---|
| GET | `/patients/template` | downloads an example `.xlsx` |
| POST | `/patients/upload` | multipart field `file`. 200 `{processed}`, 400 file problem, 413 too large, 422 row errors |
| GET | `/patients` | `page`, `size` (max 1000), `q` (search all fields), `sort` (`patient_id`, `first_name`, `last_name`, `dob`, `gender`), `order` (`asc`/`desc`) |
| PATCH | `/patients/{id}` | any of `first_name, last_name, dob, gender`. Patient ID cannot change |
| DELETE | `/patients/{id}` | 404 if it belongs to another manager |

## Status codes used

200/201 success · 400 bad request · 401 not logged in · 403 not allowed / CSRF failed ·
404 not found · 409 conflict · 413 too large · 422 validation · 423 locked · 429 rate limit · 500 unexpected
