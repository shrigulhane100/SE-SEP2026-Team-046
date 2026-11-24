"""M3.2: Authentication and role-based access"""
import pytest
from conftest import PW, rec, register, uid

def test_register_student_ok(api):
    s = register(api, "STUDENT")
    assert s["token"]


def test_register_mentor_ok(api):
    register(api, "MENTOR")


def test_register_response_shape(api):
    e = f"x{uid()}@test.com"
    r = rec("register shape", "POST /auth/register", "valid student", 201, api.call(
        "POST", "/auth/register", json={"role": "STUDENT", "name": "Abc Def", "email": e.upper(),
        "password": PW, "roll_number": "ab" + uid()}))
    j = r.json()
    assert j["token_type"] == "bearer" and j["user"]["email"] == e  # lower-cased
    assert "password" not in str(j).lower()


@pytest.mark.parametrize("label,patch", [
    ("student without roll_number", {"roll_number": None}),
    ("short password", {"password": "short"}),
    ("password 129 chars", {"password": "a" * 129}),
    ("invalid email", {"email": "not-an-email"}),
    ("name too short", {"name": "A"}),
    ("invalid role", {"role": "HACKER"}),
    ("invalid career_objective", {"career_objective": "RICH"}),
    ("roll number too short", {"roll_number": "ab"}),
])
def test_register_validation(api, label, patch):
    body = {"role": "STUDENT", "name": "Valid Name", "email": f"v{uid()}@test.com",
            "password": PW, "roll_number": "R" + uid(), **patch}
    body = {k: v for k, v in body.items() if v is not None}
    rec(f"register {label}", "POST /auth/register", label, 422, api.call("POST", "/auth/register", json=body))


def test_register_admin_forbidden(api):
    rec("self-register admin", "POST /auth/register", "role=ADMIN", (403, 422), api.call(
        "POST", "/auth/register", json={"role": "ADMIN", "name": "Evil Admin",
        "email": f"a{uid()}@test.com", "password": PW}))


def test_register_duplicate_email(api):
    s = register(api, "STUDENT")
    rec("dup email", "POST /auth/register", s["email"], 409, api.call("POST", "/auth/register", json={
        "role": "STUDENT", "name": "Dup Man", "email": s["email"], "password": PW, "roll_number": "D" + uid()}))


def test_register_duplicate_roll(api):
    s = register(api, "STUDENT")
    rec("dup roll", "POST /auth/register", s["body"]["roll_number"], 409, api.call("POST", "/auth/register", json={
        "role": "STUDENT", "name": "Dup Roll", "email": f"d{uid()}@test.com", "password": PW,
        "roll_number": s["body"]["roll_number"]}))


def test_login_ok_and_me(api):
    s = register(api, "STUDENT")
    r = rec("login ok", "POST /auth/login", s["email"], 200, api.call("POST", "/auth/login", json={"email": s["email"], "password": PW}))
    t = r.json()["access_token"]
    me = rec("me ok", "GET /auth/me", "token", 200, api.call("GET", "/auth/me", t))
    assert me.json()["email"] == s["email"] and me.json()["role"] == "STUDENT"


def test_login_wrong_password(api):
    s = register(api, "STUDENT")
    rec("login bad pw", "POST /auth/login", "wrong", 401, api.call("POST", "/auth/login", json={"email": s["email"], "password": "WrongPass#1"}))


def test_login_unknown_user(api):
    rec("login unknown", "POST /auth/login", "nouser", 401, api.call("POST", "/auth/login", json={"email": "nobody@test.com", "password": PW}))


def test_login_missing_fields(api):
    rec("login empty body", "POST /auth/login", "{}", 422, api.call("POST", "/auth/login", json={}))


def test_me_no_token(api):
    rec("me no token", "GET /auth/me", "-", 401, api.call("GET", "/auth/me"))


def test_me_garbage_token(api):
    rec("me bad token", "GET /auth/me", "garbage", 401, api.call("GET", "/auth/me", "abc.def.ghi"))


def test_logout_revokes_token(api):
    s = register(api, "STUDENT")
    rec("logout", "POST /auth/logout", "token", 204, api.call("POST", "/auth/logout", s["token"]))
    rec("token after logout", "GET /auth/me", "revoked", 401, api.call("GET", "/auth/me", s["token"]))


def test_admin_users_rbac(api, admin, student1, mentor1):
    rec("admin users admin", "GET /admin/users", "admin", 200, api.call("GET", "/admin/users", admin["token"]))
    rec("admin users student", "GET /admin/users", "student", 403, api.call("GET", "/admin/users", student1["token"]))
    rec("admin users mentor", "GET /admin/users", "mentor", 403, api.call("GET", "/admin/users", mentor1["token"]))
    rec("admin users anon", "GET /admin/users", "-", 401, api.call("GET", "/admin/users"))


def test_admin_users_filters(api, admin, student1):
    r = rec("admin users role filter", "GET /admin/users?role=STUDENT", "role", 200,
            api.call("GET", "/admin/users", admin["token"], params={"role": "STUDENT"}))
    assert all(u["role"] == "STUDENT" for u in r.json())
    r = api.call("GET", "/admin/users", admin["token"], params={"q": student1["email"]})
    assert any(u["email"] == student1["email"] for u in r.json())
    rec("admin users bad role", "GET /admin/users?role=X", "X", 422, api.call("GET", "/admin/users", admin["token"], params={"role": "X"}))
