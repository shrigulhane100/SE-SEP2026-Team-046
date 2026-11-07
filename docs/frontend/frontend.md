# Rock Starz Frontend

Frontend for the **Student Mentoring and Career Support Platform** (Team Rock Starz, SE-SEP2026-Team-046).

---

## 1. Project Overview

IITM BS students study online from across India and often have no easy way to reach people with relevant career experience. Rock Starz is a web platform where:

- **Students** describe their guidance needs, discover mentors, send structured requests and track mentoring.
- **Mentors** (recent graduates, alumni, industry professionals, researchers, entrepreneurs, faculty) publish expertise, handle requests and guide students.
- **Admins** (placement team, programme admins) monitor aggregate participation and manage users. They never see private mentoring notes.

Core journey: **Register → Create profile → Discover mentor → Send request → Mentor accepts → Relationship becomes Active → Goals, activities, feedback → Complete.**

This repository contains the React frontend only. It currently runs against a built-in **dummy API** that follows the planned `/api/v1` backend contract.

---

## 2. Technology Stack

| Purpose | Library |
|---|---|
| UI framework | React 18 |
| Build tool / dev server | Vite 5 |
| Styling | Tailwind CSS 3 (+ PostCSS, Autoprefixer) |
| Routing | React Router 6 |
| Forms and validation | React Hook Form, Zod, @hookform/resolvers |
| Charts | Recharts |
| Animation | Motion (`motion/react`) |
| Icons | Lucide React |
| Toasts | Sonner |
| Dates | date-fns |
| Class helpers | clsx, tailwind-merge |
| Fonts | Manrope, Inter, DM Mono (Google Fonts) |

Not used: shadcn/ui and Axios. UI components are hand-written with Tailwind, and API calls use `fetch` in one file.

---

## 3. Prerequisites

- **Node.js 18 or newer** (check with `node -v`)
- **npm 9 or newer** (comes with Node; check with `npm -v`)
- Internet access for `npm install` and for Google Fonts (the app still works offline with fallback fonts)

---

## 4. Installation

```bash
# clone your team repository (or unzip the provided archive)
git clone <repo-url>
cd rock-starz-frontend

npm install
```

---

## 5. Environment Configuration

Copy the example file:

```bash
cp .env.example .env
```

| Variable | Default | Meaning |
|---|---|---|
| `VITE_USE_MOCK` | `true` | `true` uses the built-in dummy API. `false` calls the real backend. |
| `VITE_API_URL` | `http://localhost:8000/api/v1` | Base URL of the real backend (used only when `VITE_USE_MOCK=false`). |

Restart the dev server after changing `.env`. Do not put secrets in frontend env variables; anything prefixed `VITE_` is public in the browser bundle.

---

## 6. Running the Application

```bash
npm run dev
```

Open the printed URL (usually http://localhost:5173).

### Demo accounts (password: `demo123`)

| Role | Email | Notes |
|---|---|---|
| Student | student@rockstarz.dev | Alex Student |
| Mentor | mentor@rockstarz.dev | Arun Kumar, capacity 2 |
| Admin | admin@rockstarz.dev | Programme admin |

The login page has one-click demo buttons.

### Suggested demo flow

1. Log in as **Student** → *Discover Mentors* → open a mentor → *Send Mentoring Request*.
2. Log out, log in as **Mentor** → *Request Inbox* → Accept (a third accept is blocked by capacity) or Reject (confirmation dialog with optional reason).
3. Open the relationship (*My Mentees* / *My Mentoring*): add goals, log activities, pause/resume, complete, give feedback.
4. Log in as **Admin** → overview charts, users, mentor verification, requests, relationships, guidance areas, analytics.
5. Register a new mentor account: it stays **Pending** and is hidden from discovery until an admin verifies it.
6. Expiry demo: one seeded request is older than 48 hours and is auto-marked **Expired** on first load.

---

## 7. Build Instructions

```bash
npm run build      # production build into dist/
npm run preview    # serve the build locally (http://localhost:4173)
```

Deploy the `dist/` folder to any static host. Because the app uses client-side routing, configure the host to serve `index.html` for unknown paths.

---

## 8. Folder Structure

```
rock-starz-frontend/
├── public/                 logo.svg
├── index.html              entry HTML, Google Fonts
├── .env.example            environment variable template
├── tailwind.config.js      brand colours, portal accents, fonts
├── vite.config.js
└── src/
    ├── main.jsx            app bootstrap (Router, AuthProvider, Toaster)
    ├── App.jsx             all routes (public + 3 protected portals)
    ├── index.css           Tailwind layers, glass/hero utilities
    ├── api/
    │   ├── client.js       single network layer (mock or real fetch)
    │   ├── mockServer.js   dummy FastAPI-style backend: routes, RBAC, business rules
    │   ├── db.js           seed data + localStorage persistence
    │   └── errors.js       ApiError
    ├── services/           thin API wrappers (auth, mentor, request, relationship, profile, notification, admin)
    ├── contexts/           AuthContext (user, login, register, logout)
    ├── hooks/              useAuth, useAsync (loading/error/data), useDebounce
    ├── routes/             ProtectedRoute (role guard)
    ├── config/nav.js       sidebar items and per-portal accent colours
    ├── lib/utils.js        helpers (cn, dates, labels, toast wrapper)
    ├── components/
    │   ├── ui/             Button, Card, Input, Select, Dialog, Tabs, Progress, Avatar, Switch, ...
    │   ├── common/         StatCard, StatusBadge, MentorCard, RequestCard, RelationshipCard, States, NotificationBell
    │   └── layout/         PublicLayout, DashboardLayout (collapsible sidebar, topbar)
    └── pages/
        ├── public/         Landing, Explore, How it works, About
        ├── auth/           Login, Register
        ├── student/        Dashboard, Discover, MentorDetail, Requests, Mentoring, Profile
        ├── mentor/         Dashboard, Inbox, Profile, Feedback
        ├── admin/          Dashboard, Users, Verification, Monitoring, Guidance, Analytics, charts
        └── shared/         Relationship, GoalsOverview, Notifications, Settings
```

---

## 9. Design System

- **Brand:** Deep Violet `#6558B8`, Deep Indigo `#292447`, Soft Lavender `#A99BEF`, Pale Lavender `#EAE5FA`, Warm Peach `#E7A17C`, Warm Ivory `#F7F5F2`.
- **Portal accents:** Student lavender `#8274D8`, Mentor teal `#397F78`, Admin slate `#435A79` (set through the `--accent` CSS variable per portal).
- **Status colours:** green accepted/completed, amber pending, red rejected, violet active, grey expired/cancelled/inactive, blue paused. Status text is always shown, not colour alone.
- **Layout:** Bento-style dashboards, selective glassmorphism on the landing page, responsive with a mobile drawer sidebar.

---

## 10. Implemented Modules

### Public
Landing page (hero, how it works, featured sample mentors, guidance areas, why Rock Starz, sample testimonials, CTA, footer), Explore Mentors, How It Works, About, Login, Register (student or mentor).

### Student portal
- **Overview:** stats, profile completion, journey steps, suggested action, current mentoring, recommended mentors, recent activity.
- **Discover Mentors:** search plus filters (guidance area, industry, mentor type, availability, experience), sort, match indicator.
- **Mentor detail:** profile, capacity, expectations note, request dialog (area, message, objective, one-time/long-term).
- **My Requests:** tabs by status, view details, cancel pending.
- **My Mentoring:** relationship list and detail (goals, activity log, pause/resume/complete, feedback, report advice).
- **Goals & Progress**, **Notifications**, **My Profile** (saves), **Settings**.

### Mentor portal
- **Overview:** stats, capacity, inbox preview, priorities, recent activities.
- **Request Inbox:** Pending / Accepted / Rejected-Expired tabs, accept, reject with confirmation and reason.
- **My Mentees**, relationship detail (can also close a relationship), **Goals & Activities**, **Feedback**, **My Profile** (expertise, max mentees, accepting toggle), **Notifications**, **Settings**.

### Admin portal
- **Overview:** totals, acceptance rate, registrations chart, request status donut, popular areas, recent activity.
- **User Management** (search, filter, activate/deactivate), **Mentor Verification**, **Mentoring Requests** (metadata only), **Active Relationships** (counts only) plus advice reports, **Guidance Areas** (add, activate/deactivate), **Reports & Analytics** (period filter), **Settings**.

### Business rules enforced in the dummy API
- Requests expire after 48 hours (scheduler runs before each call).
- One pending request per student-mentor pair; message at least 20 characters.
- Mentor capacity counts active and paused relationships.
- A request creates at most one relationship.
- Request states: `PENDING → ACCEPTED | REJECTED | EXPIRED | CANCELLED`. Relationship states: `ACTIVE ↔ PAUSED → COMPLETED | CLOSED`.
- Feedback rating 1 to 5; admins see aggregates only; accounts are deactivated, never deleted.

---

## 11. Connecting the Real Backend

1. Set `VITE_USE_MOCK=false` and `VITE_API_URL` in `.env`.
2. Make the backend match the contract in `src/api/mockServer.js` (paths, uppercase enums, JSON shapes).
3. Auth: `POST /auth/login` returns `{ access_token, user }`; the token is sent as `Authorization: Bearer <token>`.
4. Errors should use `{ "detail": "message" }` (FastAPI style); a 401 logs the user out.
5. Enable CORS for the frontend origin on the backend.

Endpoint groups: Auth, Reference (`/guidance-areas`, `/meta`), Profile and `/dashboard`, Discovery (`/mentors`), Requests, Relationships/goals/activities/feedback, Notifications, Admin. See the README in the project for the full list.

Note: your documents mention both Flask and FastAPI. Confirm the final backend with the team; the frontend only depends on the REST contract.

---

## 12. Known Limitations

- **No real backend.** All data comes from the dummy API and is stored in the browser's localStorage. It is per browser and can be cleared. Use *Settings → Reset demo data* to restore the seed data.
- **Passwords and tokens are fake** (plain text, `mock-jwt.<id>`). Frontend route guards are UX only; the real backend must enforce RBAC.
- **Notifications are in-app only** (polled every 20 seconds); no email or push.
- **No chat or calendar/session scheduling.**
- Mentor verification only approves or rejects; no document upload.
- Admin cannot create admin accounts or edit users beyond activate/deactivate.
- Landing page mentors and testimonials are **sample content**, not real people.
- No automated tests or CI yet; the bundle is a single chunk (~1 MB, ~295 KB gzip) with no code splitting.
- Google Fonts need internet access.
- Accessibility basics are in place (labels, roles, text status) but a full audit has not been done.

---

## 13. Troubleshooting

| Problem | Fix |
|---|---|
| `npm install` fails | Use Node 18+, delete `node_modules` and `package-lock.json`, retry. |
| Blank page after login | Clear localStorage for the site (or use *Reset demo data*). |
| Env change not applied | Restart `npm run dev`. |
| 404 on refresh after deploying | Configure SPA fallback to `index.html`. |
| Port 5173 busy | Vite picks the next port, or run `npm run dev -- --port 3000`. |
