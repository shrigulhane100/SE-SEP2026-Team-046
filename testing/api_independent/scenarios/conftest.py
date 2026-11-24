"""Shared fixtures for the Rock Starz end-to-end API tests.

The tests talk to a RUNNING backend over HTTP (E2E_BASE_URL, default http://127.0.0.1:8000).
They create their own uniquely named users and guidance areas on every run, so they can be
re-run safely. Use a dedicated test database, not production data.
A direct database connection (from backend/.env) is used only for things the API cannot do:
creating administrators, deactivating accounts and back-dating a request to test expiry.
"""
import itertools
import os
import sys
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import requests

# Make the backend's `app` package importable (only needed for the optional DB fixtures).
# Default: <repo>/backend. Override with E2E_BACKEND_DIR.
BACKEND_DIR = Path(os.environ.get("E2E_BACKEND_DIR") or Path(__file__).resolve().parents[3] / "backend")
sys.path.insert(0, str(BACKEND_DIR))

from .helpers import MSG, Actor, Client, ok

BASE = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
RUN = uuid.uuid4().hex[:8]
_n = itertools.count(1)
RESULTS: list[tuple[str, str, str]] = []  # (module, test, outcome) for the markdown report


def pytest_sessionstart(session):
    try:
        r = requests.get(f"{BASE}/api/v1/health", timeout=5)
        assert r.status_code == 200 and r.json()["database"] == "reachable"
    except Exception as e:  # noqa: BLE001
        pytest.exit(f"\nBackend not reachable at {BASE} ({e}).\nStart it first: uvicorn app.main:create_app --factory --port 8000\n", returncode=2)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    out = yield
    rep = out.get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.outcome != "passed"):
        RESULTS.append((item.module.__name__.split(".")[-1], item.name, rep.outcome.upper() if rep.when == "call" else "ERROR"))


def pytest_sessionfinish(session, exitstatus):
    if not RESULTS:
        return
    out = Path(__file__).parent / "report"
    out.mkdir(exist_ok=True)
    total = len(RESULTS)
    passed = sum(1 for *_, o in RESULTS if o == "PASSED")
    lines = [f"# Rock Starz E2E report", "", f"- Run id: `{RUN}`  - Server: `{BASE}`  - Time: {datetime.now():%Y-%m-%d %H:%M:%S}",
             f"- **Result: {passed}/{total} passed**", "", "| Area | Passed | Failed |", "|---|---|---|"]
    by: dict[str, list[str]] = {}
    for mod, _, o in RESULTS:
        by.setdefault(mod, []).append(o)
    for mod, os_ in by.items():
        lines.append(f"| {mod} | {os_.count('PASSED')} | {len(os_) - os_.count('PASSED')} |")
    bad = [(m, t, o) for m, t, o in RESULTS if o != "PASSED"]
    if bad:
        lines += ["", "## Failures", ""] + [f"- `{m}::{t}` ({o})" for m, t, o in bad]
    (out / "e2e-report.md").write_text("\n".join(lines) + "\n")
    print(f"\nReport written to {out / 'e2e-report.md'}")


# ---------------------------------------------------------------- database (optional)
@pytest.fixture(scope="session")
def db():
    try:
        from sqlalchemy.orm import Session
        from app.config import DatabaseSettings
        from app.db import create_db_engine
        engine = create_db_engine(DatabaseSettings())
        with Session(engine) as s:
            s.connection()
            yield s
        engine.dispose()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"direct DB access unavailable ({e})")


@pytest.fixture(scope="session")
def anon():
    return Client(BASE)


@pytest.fixture(scope="session")
def run_id():
    return RUN


def unique(prefix):
    return f"{prefix}-{RUN}-{next(_n)}"


def register(payload, password="Passw0rd!x"):
    r = Client(BASE).post("/auth/register", {**payload, "password": password})
    body = ok(r, 201)
    return Actor(BASE, body["user"], body["access_token"], password)


# ---------------------------------------------------------------- admins (all staff types)
@pytest.fixture(scope="session")
def make_admin(db):
    from app.models import User, UserRole
    from app.security import hash_password

    def _make(staff_type=None):
        email, pw = f"e2e-admin-{RUN}-{next(_n)}@example.com", "AdminPass!23"
        db.add(User(name="E2E Admin", email=email, password_hash=hash_password(pw), role=UserRole.ADMIN, staff_type=staff_type))
        db.commit()
        r = Client(BASE).post("/auth/login", {"email": email, "password": pw})
        body = ok(r)
        return Actor(BASE, body["user"], body["access_token"], pw)
    return _make


@pytest.fixture(scope="session")
def admin(make_admin):
    """Administrator. Uses E2E_ADMIN_EMAIL/E2E_ADMIN_PASSWORD if set, otherwise creates one via the DB."""
    e, p = os.environ.get("E2E_ADMIN_EMAIL"), os.environ.get("E2E_ADMIN_PASSWORD")
    if e and p:
        body = ok(Client(BASE).post("/auth/login", {"email": e, "password": p}))
        return Actor(BASE, body["user"], body["access_token"], p)
    return make_admin("PROGRAMME_ADMIN")


# ---------------------------------------------------------------- guidance areas
@pytest.fixture(scope="session")
def areas(admin):
    """Three fresh active guidance areas created by the admin."""
    return [ok(admin.api.post("/admin/guidance-areas", {"name": f"E2E {n} {RUN}", "category": "E2E"}), 201) for n in ("Alpha", "Beta", "Gamma")]


@pytest.fixture(scope="session")
def area_a(areas): return areas[0]
@pytest.fixture(scope="session")
def area_b(areas): return areas[1]
@pytest.fixture(scope="session")
def area_c(areas): return areas[2]


# ---------------------------------------------------------------- user factories
def student_profile(area_ids, **kw):
    return {"academic_level": "Diploma", "education": "BS Data Science", "career_stage": "Diploma level", "career_objective": "PLACEMENT",
            "interests": "AI and software", "goals_summary": "Get an internship", "preferred_mode": "Online", "skills": ["Python", "SQL"], "area_ids": area_ids, **kw}


def mentor_profile(area_ids, **kw):
    return {"mentor_type": "Industry Professional", "industry": f"Ind{RUN}", "current_role": "Engineer", "organisation": "Acme", "past_roles": ["Intern"],
            "experience_years": 5, "bio": "I mentor students on careers.", "education": "B.Tech", "skills": ["Python", "Design"],
            "max_mentees": 3, "is_accepting": True, "area_ids": area_ids, **kw}


@pytest.fixture
def new_student(areas):
    def _make(area_ids=None, complete=True, objective="PLACEMENT", **profile):
        s = register({"role": "STUDENT", "name": f"Student {next(_n)}", "email": f"{unique('stu')}@example.com", "roll_number": f"E2E{RUN}{next(_n)}", "career_objective": objective})
        if complete:
            ok(s.api.put("/profile/me", student_profile(area_ids if area_ids is not None else [areas[0]["id"]], career_objective=objective, **profile)))
        return s
    return _make


@pytest.fixture
def new_mentor(areas, admin):
    def _make(area_ids=None, verify=True, mentor_type="Industry Professional", complete=True, **profile):
        m = register({"role": "MENTOR", "name": f"Mentor {next(_n)}", "email": f"{unique('men')}@example.com", "mentor_type": mentor_type})
        if complete:
            ok(m.api.put("/profile/me", mentor_profile(area_ids if area_ids is not None else [a["id"] for a in areas[:2]], mentor_type=mentor_type, **profile)))
        if verify:
            ok(admin.api.post(f"/admin/mentors/{m.id}/verify", {"approve": True}))
        return m
    return _make


@pytest.fixture
def send_request(areas):
    def _send(student, mentor, area_id=None, type="LONG_TERM", message=MSG, objective="Land a good internship"):
        return ok(student.api.post("/requests", {"mentor_id": mentor.id, "area_id": area_id or areas[0]["id"], "message": message, "objective": objective, "type": type}), 201)
    return _send


@pytest.fixture
def active_pair(new_student, new_mentor, send_request):
    """A student and mentor with an accepted request: returns (student, mentor, request, relationship)."""
    def _make(**mentor_kw):
        s, m = new_student(), new_mentor(**mentor_kw)
        req = send_request(s, m)
        rel = ok(m.api.post(f"/requests/{req['id']}/accept"))["relationship"]
        return s, m, req, rel
    return _make


@pytest.fixture
def expire_request(db):
    """Back-date a request's expiry in the database to simulate 48h passing."""
    from sqlalchemy import update
    from app.models import MentoringRequest

    def _expire(request_id):
        db.execute(update(MentoringRequest).where(MentoringRequest.request_id == request_id).values(expires_at=datetime.now(UTC) - timedelta(minutes=5)))
        db.commit()
    return _expire
