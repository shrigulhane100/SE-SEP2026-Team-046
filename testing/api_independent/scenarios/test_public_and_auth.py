"""Unauthenticated access, registration, login, sessions and token handling for every role."""
import pytest
from .conftest import RUN, register, unique
from .helpers import CAREER_OBJECTIVES, MENTOR_TYPES, Client, fail, ok


def test_health_and_openapi(anon):
    assert ok(anon.get("/health")) == {"status": "ok", "database": "reachable"}
    spec = anon.s.get(f"{anon.base}/openapi.json", timeout=10).json()
    assert any(p.startswith("/api/v1/requests") for p in spec["paths"])


def test_cors_preflight_allows_frontend_origin(anon):
    r = anon.s.options(f"{anon.base}/api/v1/auth/login", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert r.status_code == 200 and r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_public_reference_data_needs_no_login(anon, areas):
    assert any(a["id"] == areas[0]["id"] for a in ok(anon.get("/guidance-areas")))
    meta = ok(anon.get("/meta"))
    assert set(CAREER_OBJECTIVES) <= set(meta["career_objectives"]) and "Faculty" in meta["mentor_types"]
    assert isinstance(ok(anon.get("/public/mentors")), list)


@pytest.mark.parametrize("objective", CAREER_OBJECTIVES)
def test_student_registers_with_each_career_objective(objective):
    s = register({"role": "STUDENT", "name": "Stu Dent", "email": f"{unique('obj')}@example.com", "roll_number": f"R{RUN}{objective[:3]}", "career_objective": objective})
    assert s.user["role"] == "STUDENT" and s.user["is_active"] is True and s.user["verification_status"] is None
    assert ok(s.api.get("/profile/me"))["profile"]["career_objective"] == objective


@pytest.mark.parametrize("mtype", MENTOR_TYPES)
def test_mentor_registers_as_each_mentor_type_and_starts_pending(mtype):
    m = register({"role": "MENTOR", "name": "Men Tor", "email": f"{unique('mt')}@example.com", "mentor_type": mtype})
    assert m.user["role"] == "MENTOR" and m.user["verification_status"] == "PENDING"


def test_register_response_shape_and_email_normalised(anon):
    email = f"{unique('Case')}@Example.COM"
    body = ok(anon.post("/auth/register", {"role": "STUDENT", "name": "  Case Test ", "email": email, "password": "Passw0rd!x", "roll_number": f" e2e{RUN}case "}), 201)
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["email"] == email.lower() and body["user"]["name"] == "Case Test"
    assert "password" not in str(body).lower().replace("password_", "")
    # duplicate e-mail differing only by case, and duplicate roll number
    fail(anon.post("/auth/register", {"role": "STUDENT", "name": "Dup", "email": email.upper(), "password": "Passw0rd!x", "roll_number": "ZZZ99999"}), 409, "email")
    fail(anon.post("/auth/register", {"role": "STUDENT", "name": "Dup", "email": f"{unique('d')}@example.com", "password": "Passw0rd!x", "roll_number": f"E2E{RUN}CASE"}), 409, "roll number")


def test_admin_cannot_self_register(anon):
    fail(anon.post("/auth/register", {"role": "ADMIN", "name": "Evil Admin", "email": f"{unique('ea')}@example.com", "password": "Passw0rd!x"}), 403, "self-register")


@pytest.mark.parametrize("payload", [
    {"role": "STUDENT", "name": "A", "email": "a@example.com", "password": "Passw0rd!x", "roll_number": "ROLL1234"},   # name too short
    {"role": "STUDENT", "name": "Ab", "email": "not-an-email", "password": "Passw0rd!x", "roll_number": "ROLL1234"},
    {"role": "STUDENT", "name": "Ab", "email": "a@example.com", "password": "short", "roll_number": "ROLL1234"},
    {"role": "STUDENT", "name": "Ab", "email": "a@example.com", "password": "Passw0rd!x"},                              # roll number required
    {"role": "STUDENT", "name": "Ab", "email": "a@example.com", "password": "Passw0rd!x", "roll_number": "AB"},
    {"role": "STUDENT", "name": "Ab", "email": "a@example.com", "password": "Passw0rd!x", "roll_number": "ROLL1234", "career_objective": "BILLIONAIRE"},
    {"role": "TEACHER", "name": "Ab", "email": "a@example.com", "password": "Passw0rd!x"},
    {"name": "Ab", "email": "a@example.com", "password": "Passw0rd!x"},
    {"role": "MENTOR", "name": "Ab", "email": "a@example.com", "password": "x" * 129},
], ids=["short-name", "bad-email", "short-password", "no-roll", "short-roll", "bad-objective", "bad-role", "no-role", "long-password"])
def test_registration_validation_errors(anon, payload):
    r = anon.post("/auth/register", payload)
    body = fail(r, 422)
    assert "password" not in r.text.lower() or "Passw0rd" not in r.text  # never echo submitted passwords


def test_login_me_logout_cycle_for_student_and_mentor(new_student, new_mentor, anon):
    for actor in (new_student(), new_mentor()):
        body = ok(anon.post("/auth/login", {"email": actor.email.upper(), "password": actor.password}))  # case-insensitive e-mail
        assert body["user"]["id"] == actor.id and body["user"]["role"] == actor.role
        c = Client(anon.base, body["access_token"])
        assert ok(c.get("/auth/me"))["email"] == actor.email
        ok(c.post("/auth/logout"), 204)
        fail(c.get("/auth/me"), 401)               # revoked session
        ok(Client(anon.base, actor.token).get("/auth/me"))  # a second session from registration stays valid


def test_admin_login_and_staff_types(make_admin, anon):
    for staff in ("PLACEMENT_TEAM", "PROGRAMME_ADMIN", "FACULTY_TA"):
        a = make_admin(staff)
        me = ok(a.api.get("/auth/me"))
        assert me["role"] == "ADMIN" and me["staff_type"] == staff and me["verification_status"] is None


def test_bad_credentials(new_student, anon):
    s = new_student()
    fail(anon.post("/auth/login", {"email": s.email, "password": "wrong-password"}), 401)
    fail(anon.post("/auth/login", {"email": f"nobody-{RUN}@example.com", "password": "Passw0rd!x"}), 401)
    fail(anon.post("/auth/login", {"email": s.email}), 422)
    # identical message for unknown user and wrong password (no account enumeration)
    a = anon.post("/auth/login", {"email": s.email, "password": "nope"}).json()
    b = anon.post("/auth/login", {"email": f"nobody-{RUN}@example.com", "password": "nope"}).json()
    assert a == b


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer garbage"}, {"Authorization": "Bearer "}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer a.b.c"}])
def test_invalid_or_missing_token_is_401(anon, headers):
    assert anon.get("/auth/me", headers=headers).status_code == 401


def test_deactivated_account_is_blocked_everywhere(new_student, anon, db):
    from sqlalchemy import update
    from app.models import User
    s = new_student()
    ok(s.api.get("/auth/me"))
    db.execute(update(User).where(User.user_id == s.id).values(is_active=False)); db.commit()
    fail(s.api.get("/auth/me"), 403, "deactivated")
    fail(anon.post("/auth/login", {"email": s.email, "password": s.password}), 403, "deactivated")
    db.execute(update(User).where(User.user_id == s.id).values(is_active=True)); db.commit()
    ok(s.relogin().api.get("/auth/me"))
