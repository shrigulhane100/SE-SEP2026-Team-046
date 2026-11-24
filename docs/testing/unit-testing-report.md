# Backend Unit Testing Report

**Project:** Student Mentoring and Career Support Platform (FastAPI + PostgreSQL, `/api/v1`)  
**Team:** Rock Starz (SE-SEP2026-Team-046) - IITM BS Software Engineering  
**Role / Owner:** Backend Unit Testing - Yash Chavan  
**Date:** 23-11-2026 | **Version:** 2.0  
**Overall Verdict:** **PASS (55 / 55 Passed, 0 Failed, 0 Defects)**

---

## 1. Executive Summary

The backend unit test suite validates backend domain logic, cryptographic security, authorization rules, and route handlers in isolation from external services. All 55 unit tests execute against an isolated test harness using pytest and in-memory mock patterns.

| Metric | Details |
|---|---|
| Test Framework | Pytest 9.2.0, AnyIO 4.16.0 |
| Test Location | `backend/tests/` (6 test files) |
| Total Tests Collected | 55 |
| Passed / Failed / Skipped | **55 / 0 / 0** |
| Execution Time | ~5.28 seconds |
| Code Coverage Areas | Auth, RBAC, Profiles, Mentors, Requests, Engagement |
| Defect Count | **0 open defects** |

---

## 2. Scope & Responsibilities

- **Owner:** Yash Chavan (Backend Developer & Unit Tester)
- **Scope Included:**
  - Password hashing with Argon2id and resistance to weak/oversized passwords.
  - JWT creation, claims validation, and signature verification with expiration enforcement.
  - Atomic transaction handling for multi-table inserts (User + Student/Mentor profile).
  - Role-based authorization filters blocking unauthorized access before database operations.
  - Profile attribute constraints (roll number formats, guidance area mappings).
  - Mentoring request rules and state validation.
  - Goal progress recalculation, activity validation, and star-rating boundaries.
- **Scope Excluded:** Live external network dependencies, browser UI rendering, stress/load testing.

---

## 3. Test Execution Breakdown by Module

```text
backend/tests/
├── test_auth.py                     (10 tests)
├── test_health.py                   (3 tests)
├── test_mentor_discovery.py         (14 tests)
├── test_mentoring.py                (6 tests)
├── test_mentoring_engagement.py     (11 tests)
└── test_profiles_and_guidance.py    (11 tests)
```

| Test File | Tests | Scenarios Covered | Result |
|---|---|---|---|
| `test_auth.py` | 10 | Argon2id hashing, expired token rejection, atomic user registration, admin self-registration blockage, password sanitization in errors, token structure, generic 401s, Bearer header parsing, student forbidden from admin lists, token revocation on logout. | **PASS** |
| `test_health.py` | 3 | Health endpoint database ping, failure response sanitization (no secret leakage), CORS preflight headers allowing frontend origin. | **PASS** |
| `test_mentor_discovery.py` | 14 | Mentor discovery listing, match score computation via guidance overlap, unavailable mentor handling, 404 for unverified mentors, query parameter validations (limit, offset, min_experience, area_id, availability, sort), role protection. | **PASS** |
| `test_mentoring.py` | 6 | Mentoring request format validation, student rejection blockage, request cancellation rules, expired request guards, relationship state transitions, student forbidden from closing relationships. | **PASS** |
| `test_mentoring_engagement.py` | 11 | Goal updates and auto-recalculation of progress, relationship active state check before goal creation, future activity date rejection, rating validation (integers 1-5), feedback authorization, unread notification counter. | **PASS** |
| `test_profiles_and_guidance.py` | 11 | Student profile field normalization, partial update persistence for mentors, invalid/wrong-role payload rejections, inactive guidance area rejection, admin guidance CRUD authorization, area deactivation. | **PASS** |
| **Total** | **55** | **100% of defined unit verification scenarios** | **PASS** |

---

## 4. Verification Evidence & Quality Artifacts

- **Unit Test Execution Log:** 55 passed in 5.28s (`backend/tests/`).
- **Test Artifacts:** `unit-test-results.xml` (JUnit XML, 55 test cases).
- **Quality Gates:** 100% pass rate achieved with zero test skips and zero failures.
- **Formal Acceptance:** Unit tests satisfy all criteria for backend implementation validation.
