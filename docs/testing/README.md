# Testing Documentation & Deliverables

Master index of testing reports, validation evidence, and quality audit records for the **Student Mentoring and Career Support Platform** (`SE-SEP2026-Team-046`).

---

## 1. Documentation Index

- [Backend Unit Testing Report](file:///c:/Users/Admin/AppData/Local/GitHubDesktop/app-3.6.6/Desktop/SE-SEP2026-Team-046/docs/testing/unit-testing-report.md): Developer-owned unit testing results (Yash Chavan, 55/55 passed).
- [API Functional Testing Report](file:///c:/Users/Admin/AppData/Local/GitHubDesktop/app-3.6.6/Desktop/SE-SEP2026-Team-046/docs/testing/api-testing-report.md): Independent functional API checks and Postman assertions (Lalithya Krishn, 162/162 checks passed).
- [End-to-End & Independent Testing Guide](file:///c:/Users/Admin/AppData/Local/GitHubDesktop/app-3.6.6/Desktop/SE-SEP2026-Team-046/docs/testing/e2e-and-independent-testing.md): Architecture of independent test suites, multi-role fixtures, RBAC matrix, and Postman verification.
- [Scenario-Based Testing Report](file:///c:/Users/Admin/AppData/Local/GitHubDesktop/app-3.6.6/Desktop/SE-SEP2026-Team-046/docs/testing/scenario-based-testing-report.md): Complete multi-role scenario results (206/206 passed, Run ID `4b414038`).
- [Defects & Retest Register](file:///c:/Users/Admin/AppData/Local/GitHubDesktop/app-3.6.6/Desktop/SE-SEP2026-Team-046/docs/testing/defects-and-retest-records.md): Formal defect log and regression records (0 open defects).

---

## 2. Test Execution Summary

| Test Level / Category | Scope | Owner | Total | Passed | Status |
|---|---|---|---|---|---|
| Backend Unit Tests | `backend/tests/` | Yash Chavan | 55 | 55 | **PASS** |
| Functional API Tests | `testing/api_functional/` | Lalithya Krishn | 95 | 95 | **PASS** |
| Independent Edge & State Tests | `testing/api_independent/` | Lalithya Krishn | 9 | 8 (1 skipped*) | **PASS** |
| Postman API Collection Assertions | `testing/api_independent/postman_results/` | Lalithya Krishn | 231 (58 req) | 231 | **PASS** |
| Multi-Role E2E Scenarios | `testing/api_independent/scenarios/` | Lalithya Krishn | 206 | 206 | **PASS** |
| **Total Automated Executions** | **All Layers** | **Team** | **596** | **595** | **PASS** |

*\*Note: 1 test (`test_expiry_after_48h`) skipped during standalone run without direct DB connection; fully passed in the comprehensive E2E scenario run (`test_request_expires_after_48_hours`).*
