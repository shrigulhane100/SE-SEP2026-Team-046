# Rock Starz Frontend (React + Vite + Tailwind)

Prototype for SE-SEP2026-Team-046. Runs fully on a **dummy API** that mirrors the planned FastAPI `/api/v1` contract, so the same code works against the real backend later.

## Run
```
npm install
npm run dev        # http://localhost:5173
```
Needs Node 18+. `npm run build` makes a production build.

## Demo accounts (password `demo123`)
| Role | Email |
|---|---|
| Student (Alex) | student@rockstarz.dev |
| Mentor (Arun, capacity 2) | mentor@rockstarz.dev |
| Admin | admin@rockstarz.dev |

Login page has one-click buttons. Data is saved in browser localStorage; **Settings > Reset demo data** restores it.

## Core flow to demo
1. Student: Discover Mentors > open a mentor > Send Request (guidance area, message, objective, one-time/long-term).
2. Mentor: Request Inbox > Accept (capacity check; a 3rd accept for Arun is blocked) or Reject (confirm dialog + reason).
3. Both: relationship page: goals, activity log, pause/resume, complete (mentor can also close), feedback; student can report advice.
4. Admin: dashboard charts, user activate/deactivate, mentor verification, requests, relationships (aggregate only), guidance areas, analytics.
5. Register a new mentor > they are PENDING until an admin verifies them (hidden from discovery until then).
6. Scheduler demo: a seeded request older than 48h is auto-marked EXPIRED on first load and both users are notified.

## Switching to the real backend
Copy `.env.example` to `.env`, set `VITE_USE_MOCK=false` and `VITE_API_URL`. Only `src/api/client.js` talks to the network; pages use `src/services/*`.
The mock in `src/api/mockServer.js` is the reference for endpoints, JSON shapes and rules:

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `/auth/register`, `GET/PATCH /auth/me`, `POST /auth/change-password` |
| Reference | `GET /guidance-areas`, `/meta` |
| Profile | `GET/PUT /profile/me`, `GET /dashboard` |
| Discovery | `GET /mentors` (q, area_id, industry, mentor_type, availability, min_experience, sort), `GET /mentors/{id}`, `GET /public/mentors` |
| Requests | `POST /requests`, `GET /requests`, `POST /requests/{id}/accept|reject|cancel` |
| Relationships | `GET /relationships[/{id}]`, `PATCH /relationships/{id}/status`, `POST .../goals`, `PATCH /goals/{id}`, `POST .../activities`, `.../feedback`, `.../report`, `GET /feedback` |
| Notifications | `GET /notifications`, `POST /notifications/{id}/read`, `/notifications/read-all` |
| Admin | `GET /admin/stats?days=`, `/admin/activity`, `/admin/users`, `PATCH /admin/users/{id}`, `/admin/mentor-verifications`, `POST /admin/mentors/{id}/verify`, `/admin/requests`, `/admin/relationships`, `/admin/reports`, `/admin/guidance-areas` |

Enums are uppercase: roles `STUDENT|MENTOR|ADMIN`; request `PENDING|ACCEPTED|REJECTED|EXPIRED|CANCELLED`; relationship `ACTIVE|PAUSED|COMPLETED|CLOSED`; errors use FastAPI style `{ "detail": "message" }`.
Frontend route guards are UX only: the backend must enforce RBAC (the mock does).

## Business rules implemented
48h request expiry; one pending request per student-mentor pair; mentor capacity counts ACTIVE + PAUSED; request creates at most one relationship; rating 1-5; admin endpoints return aggregates only (no messages, goals text or notes); deactivate instead of delete.

## Structure
`src/api` mock server + client · `src/services` API wrappers · `src/contexts` auth · `src/components/{ui,common,layout}` shared components · `src/pages/{public,auth,student,mentor,admin,shared}` · `src/routes` protected routes · `src/config/nav.js` sidebars and role accents.
