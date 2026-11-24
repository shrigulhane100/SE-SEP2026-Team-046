# REST API Specification

Comprehensive API contract for the **Rock Starz Backend** (`/api/v1`).

---

## 1. Global Conventions

- **Base URL:** `http://127.0.0.1:8000/api/v1`
- **Request & Response Format:** `application/json; charset=utf-8`
- **Authentication Header:** `Authorization: Bearer <access_token>`
- **Error Format:**
  ```json
  {
    "detail": "Descriptive human-readable error explanation"
  }
  ```
- **Validation Error Format (HTTP 422):**
  ```json
  {
    "detail": [
      {
        "loc": ["body", "field_name"],
        "msg": "Field is required or fails validation constraint",
        "type": "value_error"
      }
    ]
  }
  ```

---

## 2. API Endpoints Catalog

### 2.1 System & Health

#### `GET /health`
Verifies backend service operational state and database connection.
- **Access:** Public (Anonymous)
- **Response 200 OK:**
  ```json
  {
    "status": "ok",
    "database": "reachable"
  }
  ```
- **Response 503 Service Unavailable:** Database connectivity failure (no credentials or internal host addresses leaked).

---

### 2.2 Authentication & Sessions

#### `POST /auth/register`
Creates a new student or mentor account atomically with their corresponding profile record.
- **Access:** Public (Admin accounts cannot self-register; HTTP 403)
- **Request Body (Student):**
  ```json
  {
    "role": "STUDENT",
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "password": "StrongPassword#2026",
    "roll_number": "21F1000123",
    "career_objective": "PLACEMENT"
  }
  ```
- **Request Body (Mentor):**
  ```json
  {
    "role": "MENTOR",
    "name": "Dr. Alan Turing",
    "email": "alan.turing@example.com",
    "password": "StrongPassword#2026",
    "mentor_type": "Industry Professional"
  }
  ```
- **Response 201 Created:** Returns user details and session Bearer `access_token`.
- **Errors:** `409 Conflict` (Email or roll number duplicate), `422 Unprocessable Entity` (Password < 8 or > 128 characters, invalid email syntax, missing roll number for students).

#### `POST /auth/login`
Authenticates credentials and issues a revocable JWT bearer token.
- **Request Body:** `{"email": "user@example.com", "password": "StrongPassword#2026"}`
- **Response 200 OK:** `{"access_token": "...", "token_type": "bearer", "user": {...}}`
- **Errors:** `401 Unauthorized` (Generic "Incorrect email or password").

#### `GET /auth/me`
Retrieves currently authenticated user account and role details.
- **Access:** Authenticated (Bearer token required)
- **Response 200 OK:** User profile record.

#### `POST /auth/logout`
Revokes the caller's active session token in the database.
- **Access:** Authenticated
- **Response 204 No Content:** Token successfully invalidated. Subsequent requests using the same token fail with `401 Unauthorized`.

---

### 2.3 Profiles & Guidance Areas

#### `GET /guidance-areas`
Public directory of active guidance areas.
- **Access:** Public
- **Response 200 OK:** Array of guidance areas `[{"id": 1, "name": "Software Engineering", ...}]`.

#### `GET /profile/me`
Retrieves the profile of the authenticated student or mentor.
- **Access:** Authenticated (Student or Mentor). Admins have no profile (`404 Not Found`).

#### `PUT /profile/me`
Updates profile details and guidance area selections.
- **Access:** Authenticated
- **Student Payload:** `{"academic_level": "BS Degree", "career_objective": "PLACEMENT", "area_ids": [1, 2]}`
- **Mentor Payload:** `{"max_mentees": 5, "is_accepting": true, "bio": "...", "area_ids": [1, 3]}`
- **Errors:** `422 Unprocessable Entity` (Cross-role fields rejected, `max_mentees` < 1 or > 20), `409 Conflict` (`max_mentees` cannot be set lower than currently active mentees).

---

### 2.4 Mentor Discovery Engine

#### `GET /mentors`
Searches, filters, and paginates verified mentors.
- **Access:** Authenticated Students
- **Query Parameters:**
  - `q`: Search string across mentor name, bio, designation, and company (max 100 chars).
  - `area_ids`: Comma-separated guidance area IDs.
  - `mentor_type`: Recent Graduate, Industry Professional, Research Mentor, Entrepreneur, Faculty.
  - `career_objective`: Matches mentor guidance overlap.
  - `min_experience`: Integer (0-60).
  - `available_only`: Boolean (filters by `is_accepting` and capacity > active mentees).
  - `sort`: `experience_desc`, `match_score_desc`.
  - `limit`: Integer (1-100, default 20).
  - `offset`: Integer (>= 0).
- **Response 200 OK:** List of mentors including computed `match_score` (percentage overlap between student guidance needs and mentor expertise).

#### `GET /mentors/{id}`
Returns complete public mentor profile.
- **Response 200 OK:** Mentor object.
- **Response 404 Not Found:** Unverified or deactivated mentors return 404 to non-admins.

---

### 2.5 Mentoring Requests & Relationships

#### `POST /requests`
Submits a structured mentoring request to an available, verified mentor.
- **Access:** Authenticated Student
- **Request Body:**
  ```json
  {
    "mentor_id": 12,
    "type": "LONG_TERM",
    "objective": "Mock interview and career path preparation",
    "message": "Hello, I am interested in your guidance regarding full-stack roles."
  }
  ```
- **Errors:** `409 Conflict` (Duplicate pending request to the same mentor), `409 Conflict` (Mentor currently at full capacity), `404 Not Found` (Target mentor does not exist or unverified).

#### `GET /requests`
Returns the caller's request inbox (`status` filter supported).

#### `POST /requests/{id}/accept`
Accepts a request and creates an active mentoring relationship.
- **Access:** Mentor only (Target mentor of request).
- **Errors:** `403 Forbidden` (Student or non-recipient calls accept), `409 Conflict` (Request already processed, or mentor at full capacity).

#### `POST /requests/{id}/reject`
Rejects a request with an optional reason message.
- **Access:** Mentor only.

#### `POST /requests/{id}/cancel`
Cancels a pending request.
- **Access:** Student who created the request only.

#### `GET /relationships` & `GET /relationships/{id}`
Lists or retrieves active/past relationships for the authenticated student or mentor. Non-participants receive `404 Not Found`.

#### `PATCH /relationships/{id}/status`
Transitions relationship status.
- **Status Options:** `ACTIVE`, `PAUSED`, `COMPLETED`, `CLOSED`.
- **Business Rules:**
  - `PAUSED` occupies capacity until formally `CLOSED` or `COMPLETED`.
  - `CLOSED` is strictly a **mentor-only** action (students receive `403 Forbidden`).
  - Terminal statuses (`COMPLETED`, `CLOSED`) are permanent and cannot be reopened (`409 Conflict`).

---

### 2.6 Engagement: Goals, Activities, Feedback & Notifications

#### `POST /relationships/{id}/goals` & `PATCH /goals/{id}`
Creates and updates goals with target dates and progress percentages (0-100%). Blocked with `409 Conflict` if relationship is closed or completed.

#### `POST /relationships/{id}/activities`
Logs interactions (`MEETING`, `RESUME_REVIEW`, `MOCK_INTERVIEW`, `CHECK_IN`, `OTHER`). Blocked on closed relationships.

#### `POST /relationships/{id}/feedback`
Submits star ratings (`rating`: integer 1-5) and written feedback. Permitted even after relationship closure to facilitate final evaluation.

#### `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`
Retrieves in-app event notifications and updates read status.

---

### 2.7 Administration Portal

- `GET /admin/users`: User search and role filtering.
- `GET /admin/guidance-areas`: Complete guidance area catalog (including deactivated).
- `POST /admin/guidance-areas`: Creates new guidance area.
- `PATCH /admin/guidance-areas/{id}`: Renames or deactivates guidance area.
- `GET /admin/mentor-verifications`: Lists pending mentor verification submissions.
- `POST /admin/mentors/{id}/verify`: Approves or rejects mentor verification (`{"is_verified": true}`).
