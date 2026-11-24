# Backend Setup & Deployment Guide

Step-by-step instructions for configuring, deploying, and operating the **Rock Starz Backend** service.

---

## 1. Prerequisites

Before installing the backend, verify that your environment satisfies:

- **Python:** Version `3.12` or newer (`python --version`)
- **PostgreSQL Database:** PostgreSQL `14` or newer running locally or in Docker (`psql --version`)
- **Package Manager:** `pip` version `24+`

---

## 2. PostgreSQL Provisioning

Connect to PostgreSQL as a superuser (`postgres`) using `psql` or pgAdmin:

```sql
-- 1. Create a dedicated application role
CREATE ROLE rockstarz_app LOGIN PASSWORD 'StrongDbPassword#2026';

-- 2. Create the development database owned by the application role
CREATE DATABASE rockstarz_dev OWNER rockstarz_app;

-- 3. Grant schema permissions
GRANT ALL PRIVILEGES ON DATABASE rockstarz_dev TO rockstarz_app;
```

---

## 3. Environment Installation

From the repository root directory:

```bash
# Navigate to backend directory
cd backend

# Create isolated Python virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows Command Prompt:
# .venv\Scripts\activate.bat
# Linux / macOS:
# source .venv/bin/activate

# Install backend dependencies
pip install -r requirements-dev.txt
# Alternatively, from root: pip install -r ../requirements.txt
```

---

## 4. Environment Variables Configuration

Copy the example environment configuration to `.env`:

```bash
cp .env.example .env
```

Open `backend/.env` and configure the following parameters:

| Variable | Required | Example Value | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | `postgresql+psycopg://rockstarz_app:StrongDbPassword#2026@127.0.0.1:5432/rockstarz_dev` | PostgreSQL connection string using the psycopg3 driver. Special characters in passwords must be URL-encoded. |
| `JWT_SECRET` | **Yes** | `d4e5f6a1b2c3...` *(min 32 random characters)* | Cryptographic secret key used to sign and verify HMAC-SHA256 JWT access tokens. |
| `JWT_EXPIRY_MINUTES` | No | `60` | Lifespan of access tokens in minutes (default is 60). |
| `CORS_ORIGINS` | **Yes** | `["http://localhost:5173","http://127.0.0.1:5173"]` | JSON array of permitted browser origin URLs allowed to make cross-origin requests. |

### Generating a Secure JWT Secret
Execute the following Python snippet in your terminal:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Paste the generated output as the value for `JWT_SECRET` in `.env`.

---

## 5. Applying Database Migrations

Apply the complete schema versioning history using Alembic:

```bash
# Execute from backend directory with virtual environment active
alembic upgrade head
```

Verify successful execution:
```bash
alembic current
# Expected output: 0005 (head)
```

---

## 6. Creating the First Administrator Account

Because public registration for the `ADMIN` role is blocked by design, the initial administrator must be seeded using the interactive CLI utility:

```bash
python -m app.create_admin
```

Follow the interactive prompts:
```text
Enter Administrator Name: Super Admin
Enter Administrator Email: admin@rockstarz.iitm.ac.in
Enter Administrator Password: [hidden]
Confirm Administrator Password: [hidden]
Staff Type [PROGRAMME_COORDINATOR / PLACEMENT_TEAM / FACULTY_ADVISOR / SYSTEM_ADMIN]: SYSTEM_ADMIN
[SUCCESS] Administrator account successfully created.
```

---

## 7. Running the Server

### Development Mode (with Live Hot-Reload)
```bash
uvicorn app.main:create_app --factory --reload --port 8000
```

### Production Mode
```bash
uvicorn app.main:create_app --factory --workers 4 --host 0.0.0.0 --port 8000
```

### Verification & Documentation Links
Once started, verify service availability:
- **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Interactive Reference:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema Specification:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 8. Common Troubleshooting

| Issue | Root Cause | Solution |
|---|---|---|
| `503 Service Unavailable` on `/health` | Database is unreachable or `DATABASE_URL` is misconfigured. | Check PostgreSQL service status with `pg_isready`. Verify credentials and host in `.env`. |
| `CORS Preflight Error` in browser console | Origin not present in `CORS_ORIGINS`. | Add frontend URL (e.g. `http://localhost:5173`) to `CORS_ORIGINS` in `.env`. |
| `401 Unauthorized` on valid token | Token expired, signed with outdated secret, or session was revoked. | Login via `/api/v1/auth/login` to obtain a fresh active token. |
| `psycopg.OperationalError: password authentication failed` | Password contains reserved URL characters (`#`, `@`, `%`). | URL-encode password in `DATABASE_URL` (e.g. replace `#` with `%23`). |
