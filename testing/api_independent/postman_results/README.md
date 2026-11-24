# Postman API Verification & Proofing Results

This directory contains the independent Postman API test collection and verification records for the **Student Mentoring and Career Support Platform** (`/api/v1`).

---

## 1. Artifacts

- **`rockstarz_api_collection.postman_collection.json`**: The complete export of the test suite containing 58 distinct HTTP requests grouped into 7 functional folders, featuring 231 assertions across status codes, response times, and payload schemas.

---

## 2. Test Execution Summary

Executed against the live backend (`http://127.0.0.1:8000/api/v1`):

| Metric | Postman Collection Runner | Postman CLI / Newman | Verdict |
|---|---|---|---|
| Total Requests | 58 | 58 | **PASS (58/58)** |
| Total Assertions | 231 | 231 | **PASS (231/231)** |
| Failed Requests | 0 | 0 | **0 Failures** |
| Average Latency | 61 ms | 51 ms (min: 8 ms, max: 383 ms) | **Under 2000 ms SLA** |
| Response Data | ~64.42 kB | ~64.42 kB | Verified |

### Folder Breakdown
1. **`00 Health`** (1 request): Service availability and database ping.
2. **`01 Auth`** (11 requests): User registration, duplicate conflict prevention, payload validation, admin self-registration blockage, credential verification, and token tampering.
3. **`02 Admin and Profiles`** (9 requests): Guidance area management, profile field boundaries, and admin mentor verification.
4. **`03 Discovery`** (9 requests): Search query limits, pagination bounds, guidance area filters, and mentor detail retrieval.
5. **`04 Requests`** (9 requests): Mentoring request submission, duplicate request conflict (409), inbox retrieval, accept/reject flows.
6. **`05 Relationships & Engagement`** (15 requests): Relationship state transitions (`ACTIVE`, `PAUSED`, `CLOSED`), goal progress, activity logs, and star ratings (1-5).
7. **`06 Notifications & Logout`** (4 requests): In-app notifications, mark all as read, session revocation on logout, and revoked token rejection.

---

## 3. How to Run with Newman / Postman CLI

```bash
# Install Newman
npm install -g newman

# Execute the collection
newman run rockstarz_api_collection.postman_collection.json
```
