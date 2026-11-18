# Rock Starz backend

FastAPI and PostgreSQL foundation for the student mentoring platform. The API is
versioned under `/api/v1`. The initial migration creates users, student and
mentor profiles, guidance areas, and both profile-to-guidance-area mappings.
It includes verification and active status fields used by the frontend contract.
The request and relationship models will arrive with their feature APIs.

## Local setup

Use Python 3.12 and a running PostgreSQL instance. For a fresh setup, connect
with `psql` as a PostgreSQL administrator and create an empty development
database and its login.

```sql
CREATE ROLE rockstarz_app LOGIN;
\password rockstarz_app
CREATE DATABASE rockstarz_dev OWNER rockstarz_app;
```

Run the following from the repository root.

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
test -f .env || cp .env.example .env
```

Set `DATABASE_URL` in `.env` to the database connection URL, using the
`postgresql+psycopg` scheme. If the credentials contain reserved URL
characters, percent-encode them in the URL. Set `CORS_ORIGINS` to a JSON list
of allowed browser origins. The example allows the two common local Vite
origins. Application settings also accept environment variables.

```sh
alembic upgrade head
uvicorn app.main:create_app --factory --reload
```

- Swagger UI is at [localhost:8000/docs](http://localhost:8000/docs).
- The OpenAPI JSON is at [localhost:8000/openapi.json](http://localhost:8000/openapi.json).
- `GET /api/v1/health` returns `200` with `{"status":"ok","database":"reachable"}`
  after a successful database query. It returns `503` with
  `{"detail":"Database unavailable"}` if the database connection fails.

Run `python -m pytest` from `backend/` to check the health response, database
failure handling, and CORS. Run `alembic check` against the migrated
development database to check for schema drift.

## Migrations

Make schema changes in the SQLAlchemy models, generate a revision with
`alembic revision --autogenerate -m "describe the change"`, review the SQL and
constraints it will apply, and run `alembic upgrade head`. Keep each revision
in version control so another developer can build the same schema from scratch.
