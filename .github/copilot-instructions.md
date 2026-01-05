# Copilot instructions (PSYCare)

## Project overview
- Flask app using an application-factory: `psycare.create_app()` in [psycare/__init__.py](psycare/__init__.py).
- Server entrypoints:
  - Local dev: [app.py](app.py) (runs `create_app()` with `debug=True`).
  - WSGI: [wsgi.py](wsgi.py) exposes `app = create_app()`.
- UI is server-rendered Jinja templates under [templates/](templates/) and a vendored static admin theme under [ui/](ui/).
  - `create_app()` serves static files from `ui/` at `/static` (see [psycare/__init__.py](psycare/__init__.py)).

## Key components / data flow
- Auth is Flask-Login + WTForms:
  - Auth routes: [psycare/routes/auth.py](psycare/routes/auth.py)
  - Forms: [psycare/forms.py](psycare/forms.py)
  - User model + password hashing: [psycare/models.py](psycare/models.py)
- RBAC is a small decorator: `role_required("patient"|"therapist")` in [psycare/authz.py](psycare/authz.py).
  - Pattern: routes use `@role_required("...")` (not raw `@login_required`) and respond with `abort(403)` for wrong roles.
- DB is Flask-SQLAlchemy (global `db` in [psycare/extensions.py](psycare/extensions.py)); tables are created on startup (`db.create_all()` inside `create_app()`).
- Blueprints are split by audience:
  - Patient: [psycare/routes/patient.py](psycare/routes/patient.py) (`/patient/*`)
  - Therapist: [psycare/routes/therapist.py](psycare/routes/therapist.py) (`/therapist/*`)
  - Main: [psycare/routes/main.py](psycare/routes/main.py)

## Local dev workflow (Windows / PowerShell)
- Install deps: `.../.venv/Scripts/python.exe -m pip install -r requirements.txt` (see [README.md](README.md)).
- Run server: `.../.venv/Scripts/python.exe app.py` then open `http://127.0.0.1:5000`.
- Default DB: SQLite at `instance/app.db` (created on first run).
- Environment variables used by `create_app()`:
  - `SECRET_KEY`, `DATABASE_URL`, optional `PORT`, and `ALLOW_THERAPIST_REGISTER` (see [psycare/__init__.py](psycare/__init__.py)).

## Testing conventions
- Tests are pytest and build an in-memory DB via `create_app({..."SQLALCHEMY_DATABASE_URI": "sqlite://"...})`.
  - Reference: [tests/test_auth_and_crud.py](tests/test_auth_and_crud.py)
  - CSRF is disabled in tests with `WTF_CSRF_ENABLED = False`.
- Run: `.../.venv/Scripts/python.exe -m pytest -q`.

## Coding patterns to follow in this repo
- Routes:
  - Use blueprint modules in [psycare/routes/](psycare/routes/) and keep URL prefixes consistent (`/auth`, `/patient`, `/therapist`).
  - Use WTForms `validate_on_submit()` and return template + HTTP status on validation/auth errors (e.g., 400/401/409 in [psycare/routes/auth.py](psycare/routes/auth.py)).
  - Use `flash(message, category)` where `category` maps to Bootstrap alert classes (see [templates/base.html](templates/base.html)).
- DB access:
  - Prefer `db.session.get(Model, id)` for lookups by PK and `Model.query.filter_by(...)` for filtered lists.
  - On ownership checks, follow the existing pattern: fetch, verify `patient_id/therapist_id`, otherwise `abort(404)` or `abort(403)` (see [psycare/routes/patient.py](psycare/routes/patient.py) and [psycare/routes/therapist.py](psycare/routes/therapist.py)).
- Templates/static:
  - Base layout is [templates/base.html](templates/base.html); patient/therapist navigation is driven by `current_user.role`.
  - Static assets should be referenced via `url_for('static', filename=...)` (served from `ui/`).
