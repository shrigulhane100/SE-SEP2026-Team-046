# End-to-End & Independent API Testing Documentation

Comprehensive technical documentation of the independent API verification suites, multi-role scenario journeys, concurrency safety, and Postman assertion suites (`Milestone 3.8`).

---

## 1. Objectives & Testing Strategy

Independent testing provides black-box, external validation of the complete backend system against documented requirements and user stories without relying on developer unit mocks.

### Testing Principles
- **Black-Box Over HTTP:** All assertions execute over standard HTTP requests against a running FastAPI server instance (`http://127.0.0.1:8000/api/v1`).
- **Dynamic Isolation:** Tests do not depend on pre-seeded fixtures; each test scenario creates fresh, uniquely-named actors (students, mentors, admins) so test executions are completely idempotent and safe to re-run.
- **Actor-Based Modeling:** Utilizes an `Actor` abstraction that wraps an authenticated HTTP session with credentials, tokens, and role context.
- **Zero-Trust Role Verification:** Every endpoint is systematically tested against unauthorized roles and anonymous users to ensure strict boundary enforcement.

---

## 2. Test Suite Architecture

```text
testing/
├── conftest.py                   # Pytest fixtures and live HTTP connection check
├── pytest.ini                    # Unified Pytest configuration (pythonpath, testpaths)
├── README.md                     # Tester guide and visual gallery
├── requirements-tester.txt       # Dependencies for API testing
├── images/                       # Visual screenshots and proofing artifacts
├── api_functional/               # 95 Functional API checks
└── api_independent/              # Milestone 3.8 independent verification
    ├── postman_results/          # Newman / Postman verification collection (231 assertions)
    │   ├── rockstarz_api_collection.postman_collection.json
    │   └── README.md
    ├── test_edge_cases_security.py  # SQLi, boundary, and pagination tests
    ├── test_state_transitions.py    # Request/relationship state machines
    └── scenarios/                   # Multi-role journeys (206 tests)
        ├── conftest.py              # Test lifecycle hooks and DB fixtures
        ├── helpers.py               # Actor & Client wrappers, assertions
        ├── __init__.py
        ├── test_public_and_auth.py
        ├── test_rbac_matrix.py
        ├── test_admin_portal.py
        ├── test_profiles.py
        ├── test_mentor_discovery.py
        ├── test_requests.py
        ├── test_capacity_and_lifecycle.py
        ├── test_goals_activities_feedback.py
        ├── test_notifications.py
        └── test_concurrency_and_journeys.py
```

### The Actor & Client Abstraction (`helpers.py`)
- `Client`: Thin wrapper over `requests.Session` that automatically prefixes `/api/v1`, attaches Bearer headers, and enforces standard timeouts.
- `Actor`: Represents a registered user persona with its own credentials and isolated HTTP client, supporting `.relogin()` and role impersonation.
- `ok(r, code=200)` & `fail(r, code, contains=None)`: Standardized assertions validating HTTP response status codes and clean JSON error structures without leaking stack traces.

---

## 3. Detailed Scenario Modules Breakdown (206 Tests)

| Module | Tests | Key Scenarios Covered |
|---|---|---|
| `test_public_and_auth.py` | 32 | Server health & OpenAPI specs, CORS headers allowing frontend Vite origins, public reference taxonomies, student registration across all 4 career objectives (`PLACEMENT`, `HIGHER_STUDIES`, `ENTREPRENEURSHIP`, `CAREER_CLARITY`), mentor registration across all 5 classifications, 9 validation error cases, login/me/logout cycles, admin login, bad credentials, 5 token tampering cases, deactivated account blockage. |
| `test_rbac_matrix.py` | 59 | Systematic RBAC evaluation across 26 API endpoints: anonymous callers receive `401 Unauthorized` on all protected routes; student, mentor, and admin permissions verified individually; cross-role action attempts blocked with `403 Forbidden`. |
| `test_admin_portal.py` | 5 | Administrative user listing and search, staff type access validation, guidance area full CRUD, area usage counters, mentor verification approval/rejection workflows. |
| `test_profiles.py` | 27 | Student profile creation and updates, career objective persistence, 14 validation checks (academic level, invalid areas, oversized skills array), roll-number uniqueness constraints, mentor profile creation across types, max mentee reduction rules, admin profile absence check. |
| `test_mentor_discovery.py` | 18 | Public listing concealment of unverified mentors, student search with multi-parameter filtering, match score computation from guidance overlap, detail views, availability indicators, 9 query parameter boundary tests. |
| `test_requests.py` | 12 | Structured request creation (`ONE_TIME` and `LONG_TERM`), duplicate pending prevention, input validation, unverified/unavailable mentor blockage, accept and relationship creation, reject with/without reason, cancellation by student, non-participant access isolation, 48-hour expiration logic. |
| `test_capacity_and_lifecycle.py` | 11 | Mentor capacity blocking accept and new requests when full, slot occupancy during `PAUSED` state, closing relationship frees capacity slot, status transition validation, student forbidden from closing relationships (`403 Forbidden`). |
| `test_goals_activities_feedback.py` | 30 | Collaborative milestone creation by both roles, progress recalculation, 6 create and 5 update validation cases, activity logging across all types, two-way feedback and star ratings (1-5), read-only immutability of completed/closed mentorships, stranger blockage. |
| `test_notifications.py` | 8 | Empty notifications for new users, automated notification triggers across request lifecycle, cancellation/rejection alerts, relationship event notifications, notification privacy isolation, mark read / mark all read endpoints. |
| `test_concurrency_and_journeys.py` | 4 | Concurrency and race conditions: 4 parallel accepts against a mentor with capacity 1 (guarantees exactly one 200 OK and three 409 Conflict), parallel duplicate request race, double-accept race, and a complete 12-step multi-role journey from registration to completion. |

---

## 4. Postman Verification Collection (58 Requests, 231 Assertions)

The Postman verification suite (`testing/api_independent/postman_results/`) provides an automated test collection that executes via Postman Runner or Newman CLI:

- **Total Requests Executed:** 58
- **Total Assertions Evaluated:** 231
- **Passed Assertions:** **231 (100% Pass Rate)**
- **Average Response Latency:** 51 ms (well within the 2000 ms SLA requirement)
- **Error Payload Assertions:** Confirms that all 4xx error bodies include readable `detail` messages, 422 errors include field `loc` arrays, and no credentials or database details are leaked.

---

## 5. Security & Edge-Case Testing

- **SQL Injection Prevention:**
  - Login injection: `POST /auth/login` with `' OR '1'='1` returns `401 Unauthorized` without SQL execution or syntax leaks.
  - Query parameter injection: `GET /mentors?q='; DROP TABLE users;--` is safely escaped by parameterized SQLAlchemy queries, returning `200 OK` with an empty result array.
- **Tampered Token Handling:**
  - Malformed tokens, tokens signed with invalid keys, and truncated Bearer headers strictly return `401 Unauthorized`.
- **State Transition Guards:**
  - Reopening a completed relationship returns `409 Conflict`.
  - Adding goals or activities to a closed relationship returns `409 Conflict`.
  - Closing a relationship as a student returns `403 Forbidden`.
