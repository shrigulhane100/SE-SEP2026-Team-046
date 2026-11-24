# Defect and Retest Register

**Project:** Student Mentoring and Career Support Platform (FastAPI + PostgreSQL, `/api/v1`)  
**Team:** Rock Starz (SE-SEP2026-Team-046) - IITM BS Software Engineering  
**Testers:** Yash Chavan (Backend Unit Tests), Lalithya Krishn (API & Scenario Tests)  
**Date:** 23-11-2026 | **Version:** 2.0  
**Status:** **CLOSED - 0 Open Defects (100% Verified Pass)**

---

## 1. Defect Tracking Overview

All test suites—spanning developer unit tests (55), functional API tests (95), Postman request assertions (231), independent edge-case tests (9), and end-to-end scenario journeys (206)—were executed against the backend implementation.

Throughout test execution, tests were evaluated against documented specifications, role permissions, and boundary conditions.

| Severity | Logged | Resolved | Retested & Verified | Open |
|---|---|---|---|---|
| Critical (Blocker) | 0 | 0 | 0 | 0 |
| High (Major Functional) | 0 | 0 | 0 | 0 |
| Medium (Edge Cases) | 0 | 0 | 0 | 0 |
| Low (Minor / Cosmetic) | 0 | 0 | 0 | 0 |
| **Total** | **0** | **0** | **0** | **0** |

---

## 2. Observations & Verification Notes

During independent testing, minor informational items and environment observations were noted and reviewed:

| ID | Observation Description | Analysis & Verification | Status |
|---|---|---|---|
| **OBS-01** | `test_expiry_after_48h` skipped during standalone API run when direct database connection for back-dating timestamps was omitted. | Fully retested and validated in the complete multi-role scenario suite (`test_request_expires_after_48_hours` in `test_06_requests.py`), where the request expiration and notification trigger were verified end-to-end. | **VERIFIED PASS** |
| **OBS-02** | Cancelling another student's request returns HTTP `404 Not Found` rather than `403 Forbidden`. | Verified as intentional security design: returning 404 conceals resource existence from unauthorized callers, preventing ID enumeration. | **VERIFIED PASS** |
| **OBS-03** | Submitting feedback is allowed on a `CLOSED` relationship (HTTP 200), whereas adding goals or activities is blocked (HTTP 409). | Validated against requirements: students and mentors should be able to submit retrospective reviews after a mentorship concludes, but cannot add active goals or meetings. | **VERIFIED PASS** |
| **OBS-04** | Execution environment utilized Python 3.13 / 3.14 runtime. | Tested for compatibility: all core dependencies (`fastapi`, `pydantic`, `SQLAlchemy`, `psycopg`, `pwdlib`, `PyJWT`) operate cleanly with zero runtime warnings or deprecation errors. | **VERIFIED PASS** |

---

## 3. Retest & Regression Summary

- **Regression Cycles:** 3 complete test passes (Unit, Functional API + Postman, and E2E Scenarios).
- **Flakiness Assessment:** 0 flaky tests detected. Concurrent race condition tests (`test_simultaneous_accepts_never_overbook_a_mentor`, `test_simultaneous_duplicate_requests_create_only_one`) consistently yielded deterministic results.
- **Defect Acceptance:** Backend meets all functional and non-functional acceptance criteria with zero unresolved defects.
