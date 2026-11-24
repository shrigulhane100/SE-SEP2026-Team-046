"""Black-box API test harness (tester suite) for Rock Starz backend.
Runs against a LIVE server. Env vars:
  BASE_URL        default http://127.0.0.1:8000/api/v1
  ADMIN_EMAIL / ADMIN_PASSWORD   an existing admin (python -m app.create_admin)
  DATABASE_URL    optional, only for the 48-hour expiry test
Writes test_cases.csv (API, Inputs, Expected, Actual, Result) at the end.
"""
import csv, os, uuid
import httpx
import pytest

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000/api/v1")
PW = "StrongPass#2026"
RECORDS = []


def uid():
    return uuid.uuid4().hex[:8]


class Api:
    def __init__(self):
        self.c = httpx.Client(base_url=BASE, timeout=20)

    def call(self, method, path, token=None, **kw):
        h = {"Authorization": f"Bearer {token}"} if token else {}
        return self.c.request(method, path, headers=h, **kw)


@pytest.fixture(scope="session")
def api():
    a = Api()
    try:
        a.call("GET", "/health")
    except Exception as e:  # server down
        pytest.exit(f"Server not reachable at {BASE}: {e}")
    return a


def rec(name, api_desc, inputs, expected, resp, ok=None):
    """Record a test case in the required format and assert."""
    codes = expected if isinstance(expected, (tuple, list, set)) else (expected,)
    passed = resp.status_code in codes if ok is None else ok
    RECORDS.append({
        "Test": name, "API being tested": api_desc, "Inputs": str(inputs)[:300],
        "Expected output": f"HTTP {'/'.join(map(str, codes))}",
        "Actual output": f"HTTP {resp.status_code} {resp.text[:150]}",
        "Result": "Success" if passed else "Fail"})
    assert passed, f"{name}: expected {codes} got {resp.status_code} {resp.text[:300]}"
    return resp


def pytest_sessionfinish(session, exitstatus):
    if RECORDS:
        with open("test_cases.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(RECORDS[0]))
            w.writeheader(); w.writerows(RECORDS)


def register(api, role, **extra):
    e = f"{role.lower()}_{uid()}@test.com"
    body = {"role": role, "name": f"{role.title()} {uid()}", "email": e, "password": PW, **extra}
    if role == "STUDENT":
        body.setdefault("roll_number", "T" + uid().upper())
    r = api.call("POST", "/auth/register", json=body)
    assert r.status_code == 201, r.text
    j = r.json()
    return {"token": j["access_token"], "id": j["user"]["id"], "email": e, "body": body}


@pytest.fixture(scope="session")
def admin(api):
    e, p = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
    if not (e and p):
        pytest.exit("Set ADMIN_EMAIL and ADMIN_PASSWORD")
    r = api.call("POST", "/auth/login", json={"email": e, "password": p})
    assert r.status_code == 200, r.text
    return {"token": r.json()["access_token"], "id": r.json()["user"]["id"]}


@pytest.fixture(scope="session")
def areas(api, admin):
    out = []
    for n in ("A", "B"):
        r = api.call("POST", "/admin/guidance-areas", admin["token"],
                     json={"name": f"Area{n}-{uid()}", "category": "Career"})
        assert r.status_code == 201, r.text
        out.append(r.json()["id"])
    return out


def make_mentor(api, admin, area_ids, verified=True, max_mentees=3, accepting=True):
    m = register(api, "MENTOR", mentor_type="Industry Professional")
    r = api.call("PUT", "/profile/me", m["token"], json={
        "industry": "Information Technology", "current_role": "Engineer",
        "organisation": "TestCo", "experience_years": 5, "bio": "Test mentor bio",
        "skills": ["python"], "max_mentees": max_mentees, "is_accepting": accepting,
        "area_ids": area_ids})
    assert r.status_code == 200, r.text
    if verified:
        v = api.call("POST", f"/admin/mentors/{m['id']}/verify", admin["token"], json={"approve": True})
        assert v.status_code == 200, v.text
    return m


@pytest.fixture(scope="session")
def student1(api, areas):
    s = register(api, "STUDENT", career_objective="PLACEMENT")
    r = api.call("PUT", "/profile/me", s["token"], json={
        "roll_number": s["body"]["roll_number"], "academic_level": "Diploma",
        "career_objective": "PLACEMENT", "skills": ["sql"], "area_ids": [areas[0]]})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="session")
def student2(api):
    return register(api, "STUDENT")


@pytest.fixture(scope="session")
def mentor1(api, admin, areas):   # verified, capacity 1
    return make_mentor(api, admin, [areas[0]], max_mentees=1)


@pytest.fixture(scope="session")
def mentor2(api, admin, areas):   # verified, capacity 3, both areas
    return make_mentor(api, admin, areas, max_mentees=3)


@pytest.fixture(scope="session")
def mentor_unverified(api, admin, areas):
    return make_mentor(api, admin, [areas[0]], verified=False)


@pytest.fixture(scope="session")
def mentor_closed(api, admin, areas):
    return make_mentor(api, admin, [areas[0]], accepting=False)


MSG = "I would like guidance on preparing for technical interviews."


def new_request(api, student, mentor, area, type_="LONG_TERM", msg=MSG):
    return api.call("POST", "/requests", student["token"], json={
        "mentor_id": mentor["id"], "area_id": area, "message": msg,
        "objective": "Get placed", "type": type_})


def new_relationship(api, student, mentor, area):
    r = new_request(api, student, mentor, area)
    assert r.status_code == 201, r.text
    a = api.call("POST", f"/requests/{r.json()['id']}/accept", mentor["token"])
    assert a.status_code == 200, a.text
    return a.json()["relationship"]["id"], r.json()["id"]
