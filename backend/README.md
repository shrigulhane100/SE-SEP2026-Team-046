# Rock Starz backend

FastAPI and PostgreSQL backend for the student mentoring platform. The API is
versioned under `/api/v1`. The initial migration creates users, student and
mentor profiles, guidance areas, and both profile-to-guidance-area mappings.
It includes verification and active status fields used by the frontend contract.
The authentication migration adds revocable login sessions and stores the
career objective selected during student registration.

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
origins. Generate a private `JWT_SECRET` with
`python -c "import secrets; print(secrets.token_urlsafe(48))"` and set it in
`.env`. Access tokens last 60 minutes by default. Set
`JWT_EXPIRY_MINUTES` to change the duration. Application settings also
accept environment variables.

```sh
alembic upgrade head
uvicorn app.main:create_app --factory --reload
```

- Swagger UI is at [localhost:8000/docs](http://localhost:8000/docs).
- The OpenAPI JSON is at [localhost:8000/openapi.json](http://localhost:8000/openapi.json).
- `GET /api/v1/health` returns `200` with `{"status":"ok","database":"reachable"}`
  after a successful database query. It returns `503` with
  `{"detail":"Database unavailable"}` if the database connection fails.

## Authentication

Use Swagger or a JSON client to call the following endpoints.

| Method and route | Behavior |
| --- | --- |
| `POST /api/v1/auth/register` | Accepts `role`, `name`, `email`, and `password`. Students also supply `roll_number` and can supply `career_objective`. Mentors can supply `mentor_type`. Returns a bearer token and the new account. |
| `POST /api/v1/auth/login` | Accepts JSON `email` and `password` and returns a bearer token and account details. |
| `GET /api/v1/auth/me` | Returns the account for the bearer token. |
| `POST /api/v1/auth/logout` | Revokes the current session and returns HTTP 204. |
| `GET /api/v1/admin/users` | Lists accounts for administrators and accepts optional `role` and `q` filters. |

New accounts use passwords of 8 to 128 characters stored as Argon2id hashes.
In Swagger, use **Authorize** to set the token. For other clients, send
`Authorization: Bearer <token>`. Invalid, expired, and revoked tokens return
401. A disabled account or an account without the required role returns 403.

Create an administrator from an interactive terminal after applying migrations.
The command prompts privately for the password.

```sh
python -m app.create_admin --name "Programme Admin" --email admin@example.com
```

## Profiles and guidance areas

| Method and route | Behavior |
| --- | --- |
| `GET /api/v1/profile/me` | Returns the signed-in student or mentor's profile, completion percentage, and guidance-area IDs. |
| `PUT /api/v1/profile/me` | Saves the caller's profile and creates it if needed. A student creating a profile must supply `roll_number`. |
| `GET /api/v1/guidance-areas` | Lists active areas and their IDs. |
| `GET /api/v1/meta` | Lists profile form choices. |
| `GET /api/v1/admin/guidance-areas` | Lists all areas with mentor counts. Request counts are zero until the mentoring-request APIs are available. |
| `POST /api/v1/admin/guidance-areas` | Adds an area with a `name` and an optional `category`. |
| `PATCH /api/v1/admin/guidance-areas/{area_id}` | Edits an area's name, category or active status. |

Log in as an administrator to create an area before assigning it to a profile.
For profile updates, omitted fields keep their current values. Send
`area_ids` to replace the selected areas. An empty array clears the list.
Existing mappings to inactive areas are kept until the owner removes them.
Guidance area names are unique regardless of case.

## Tests

Run `python -m pytest` from `backend/` to check health responses, CORS,
authentication, role enforcement, profile updates, and guidance areas. Run `alembic check`
against the migrated development database to check for schema drift.


## Migrations

Make schema changes in the SQLAlchemy models, generate a revision with
`alembic revision --autogenerate -m "describe the change"`, review the SQL and
constraints it will apply, and run `alembic upgrade head`. Keep each revision
in version control so another developer can build the same schema from scratch.
