# Rock Starz Backend Documentation

FastAPI and PostgreSQL backend for the **Student Mentoring and Career Support Platform** (Team Rock Starz, SE-SEP2026-Team-046).

---

## 1. System Overview

The Rock Starz backend provides a secure, transactional, and performant REST API versioned under `/api/v1`. It powers the mentoring lifecycle for IITM BS students, mentors, and administrators:
- **Authentication & RBAC**: Multi-role security enforcing strict role boundaries (Anonymous, Student, Mentor, Administrator) using Argon2 password hashing and revocable JWT bearer sessions.
- **Profiles & Guidance Areas**: Distinct student and mentor profiles, academic levels, mentor classifications, and many-to-many guidance area mapping with verification workflows.
- **Discovery & Matching Engine**: High-performance querying of verified mentors with multi-attribute filtering, availability checking, and overlap-based compatibility score calculations.
- **Mentoring Lifecycle**: Structured request dispatch, 48-hour expiration handling, duplicate request prevention, mentor capacity limits, and relationship state machine (`ACTIVE`, `PAUSED`, `CLOSED`).
- **Engagement & Collaboration**: Milestone goals with progress calculations, activity logging (Meetings, Resume Reviews, Mock Interviews, Check-ins), bidirectional feedback/ratings, and in-app notifications.

---

## 2. Technology Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| Web Framework | FastAPI | `0.163.2` | High-performance asynchronous REST API framework |
| ASGI Server | Uvicorn | `0.54.0` | Production ASGI web server |
| ORM | SQLAlchemy | `2.0.58` | Object-relational mapping and connection pooling |
| Migrations | Alembic | `1.20.1` | Relational schema versioning and migrations |
| Database Driver | psycopg (v3) | `3.3.9` | High-performance PostgreSQL database adapter |
| Validation | Pydantic & Settings | `2.14.3` | Request/response schema validation and settings management |
| Password Hashing | pwdlib with Argon2 | `0.4.2` | Secure key derivation and modern password hashing |
| Session Tokens | PyJWT | `2.15.1` | Cryptographic JWT access token encoding/decoding |
| Email Validation | email-validator | `2.4.0` | RFC-compliant email address validation |

---

## 3. Database Schema & Migration Foundation

Database schema evolution is managed via Alembic in `backend/alembic/versions/`:

1. **`0001_create_account_and_profile_foundation.py`**:
   - `users`: Core account table (`id`, `role`, `name`, `email`, `password_hash`, `is_active`).
   - `student_profiles`: Student details (`roll_number`, `academic_level`, `preferred_mode`, `career_objective`).
   - `mentor_profiles`: Mentor details (`mentor_type`, `experience_years`, `company_or_institution`, `designation`, `bio`, `max_mentees`, `is_accepting`, `is_verified`).
   - `guidance_areas`: System taxonomies (`name`, `description`, `is_active`).
   - `student_guidance_areas` & `mentor_guidance_areas`: Many-to-many mappings.
2. **`0002_add_authentication_sessions.py`**:
   - `sessions`: Revocable token session table tracking active JWT identifiers and revocation timestamps.
3. **`0003_complete_profile_fields.py`**:
   - Secondary profile attributes, LinkedIn URLs, skills arrays, and communication preferences.
4. **`0004_add_mentoring_requests_and_relationships.py`**:
   - `mentoring_requests`: Request records (`student_id`, `mentor_id`, `type`, `objective`, `message`, `status`, `expires_at`).
   - `mentoring_relationships`: Active mentorships (`student_id`, `mentor_id`, `status`, `start_date`, `end_date`).
5. **`0005_add_mentoring_engagement.py`**:
   - `goals`: Relationship goals, target dates, and progress percentage.
   - `activities`: Logged mentoring interactions (`activity_type`, `notes`, `date`).
   - `feedback`: Two-way star ratings (1-5) and written feedback.
   - `notifications`: Real-time user notification queue (`user_id`, `title`, `message`, `is_read`).

---

## 4. API Endpoints Reference

All endpoints reside under `/api/v1`.

### 4.1 System & Authentication
- `GET /health`: Health and database connectivity status (`200 OK` or `503 Service Unavailable`).
- `POST /auth/register`: Register as student or mentor.
- `POST /auth/login`: Authenticate credentials and receive Bearer JWT.
- `GET /auth/me`: Retrieve currently authenticated account details.
- `POST /auth/logout`: Revoke active session token.

### 4.2 Profiles & Guidance Areas
- `GET /guidance-areas`: Public listing of active guidance areas.
- `GET /profile/me`: Retrieve caller's profile.
- `PUT /profile/me`: Update profile details and guidance area selections.

### 4.3 Mentor Discovery
- `GET /mentors`: Search, filter, and paginate verified mentors.
  - Query parameters: `q`, `area_ids`, `career_objective`, `mentor_type`, `min_experience`, `available_only`, `sort`, `limit`, `offset`.
- `GET /mentors/{id}`: Detailed public mentor profile with match analysis.

### 4.4 Mentoring Requests & Relationships
- `POST /requests`: Create structured mentoring request (`ONE_TIME` or `LONG_TERM`).
- `GET /requests`: List user's sent or received requests.
- `POST /requests/{id}/accept`: Mentor accepts request; creates relationship if capacity permits.
- `POST /requests/{id}/reject`: Mentor rejects request with optional reason.
- `POST /requests/{id}/cancel`: Student cancels pending request.
- `GET /relationships`: List relationships for student or mentor.
- `GET /relationships/{id}`: Retrieve relationship details.
- `PATCH /relationships/{id}/status`: Transition status (`ACTIVE`, `PAUSED`, `CLOSED`).

### 4.5 Engagement (Goals, Activities, Feedback, Notifications)
- `POST /relationships/{id}/goals`: Create a goal.
- `PATCH /goals/{id}`: Update goal progress or status.
- `POST /relationships/{id}/activities`: Log meeting, resume review, mock interview, or check-in.
- `POST /relationships/{id}/feedback`: Submit rating and review.
- `GET /feedback`: List feedback received.
- `GET /notifications`: List notifications for caller.
- `POST /notifications/{id}/read`: Mark notification as read.
- `POST /notifications/read-all`: Mark all notifications as read.

### 4.6 Administration Portal
- `GET /admin/users`: Search and filter user accounts.
- `GET /admin/guidance-areas`: List all guidance areas (active and inactive).
- `POST /admin/guidance-areas`: Create new guidance area.
- `PATCH /admin/guidance-areas/{id}`: Edit or deactivate guidance area.
- `GET /admin/mentor-verifications`: List pending mentor verification applications.
- `POST /admin/mentors/{id}/verify`: Approve or reject mentor profile verification.

---

## 5. Environment & Local Setup

### Prerequisites
- Python 3.12 or newer
- Running PostgreSQL database instance

### Database Setup
Connect to PostgreSQL via `psql` as superuser:
```sql
CREATE ROLE rockstarz_app LOGIN PASSWORD 'your_secure_password';
CREATE DATABASE rockstarz_dev OWNER rockstarz_app;
```

### Virtual Environment & Installation
From the repository root:
```bash
cd backend
python -m venv .venv

# Activate venv:
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements-dev.txt
```

### Environment Configuration (`backend/.env`)
Create `backend/.env` with:
```env
DATABASE_URL=postgresql+psycopg://rockstarz_app:your_secure_password@127.0.0.1:5432/rockstarz_dev
JWT_SECRET=super_secret_jwt_random_key_replace_with_crypto_safe_string
JWT_EXPIRY_MINUTES=60
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173"]
```

### Applying Migrations and Creating Initial Admin
```bash
# Apply migrations to database
alembic upgrade head

# Create administrator account interactively
python -m app.create_admin
```

### Starting the Server
```bash
uvicorn app.main:create_app --factory --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI Specification: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
