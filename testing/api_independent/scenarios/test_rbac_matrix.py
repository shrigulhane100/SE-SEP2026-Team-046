"""Role-based access control: every protected endpoint is tried as anonymous, student, mentor and admin."""
import pytest
from .helpers import MSG

# (method, path, body, allowed roles). Path ids are fake: the permission check must run BEFORE lookup,
# so allowed roles get 404/409/422 (not 401/403) and everyone else gets 401/403.
S, M, A = "STUDENT", "MENTOR", "ADMIN"
ENDPOINTS = [
    ("GET", "/auth/me", None, {S, M, A}),
    ("POST", "/auth/logout", None, {S, M, A}),
    ("GET", "/admin/users", None, {A}),
    ("GET", "/admin/guidance-areas", None, {A}),
    ("POST", "/admin/guidance-areas", {"name": "x"}, {A}),
    ("PATCH", "/admin/guidance-areas/999999", {"name": "x"}, {A}),
    ("GET", "/admin/mentor-verifications", None, {A}),
    ("POST", "/admin/mentors/999999/verify", {"approve": True}, {A}),
    ("GET", "/profile/me", None, {S, M}),
    ("PUT", "/profile/me", {}, {S, M}),
    ("GET", "/mentors", None, {S}),
    ("GET", "/mentors/999999", None, {S}),
    ("POST", "/requests", {"mentor_id": 999999, "area_id": 1, "message": MSG, "type": "ONE_TIME"}, {S}),
    ("GET", "/requests", None, {S, M}),
    ("GET", "/requests/999999", None, {S, M}),
    ("POST", "/requests/999999/accept", None, {M}),
    ("POST", "/requests/999999/reject", {}, {M}),
    ("POST", "/requests/999999/cancel", None, {S}),
    ("GET", "/relationships", None, {S, M}),
    ("GET", "/relationships/999999", None, {S, M}),
    ("PATCH", "/relationships/999999/status", {"status": "PAUSED"}, {S, M}),
    ("POST", "/relationships/999999/goals", {"title": "g"}, {S, M}),
    ("PATCH", "/goals/999999", {"status": "DONE"}, {S, M}),
    ("POST", "/relationships/999999/activities", {"activity_type": "MEETING", "notes": "n"}, {S, M}),
    ("POST", "/relationships/999999/feedback", {"rating": 5}, {S, M}),
    ("GET", "/feedback", None, {S, M}),
    ("GET", "/notifications", None, {S, M, A}),
    ("POST", "/notifications/read-all", None, {S, M, A}),
    ("POST", "/notifications/999999/read", None, {S, M, A}),
]
ids = [f"{m} {p}" for m, p, *_ in ENDPOINTS]


@pytest.mark.parametrize("method,path,body,allowed", ENDPOINTS, ids=ids)
def test_anonymous_gets_401(anon, method, path, body, allowed):
    assert anon.req(method, path, json=body).status_code == 401


@pytest.mark.parametrize("method,path,body,allowed", ENDPOINTS, ids=ids)
def test_each_role_is_allowed_or_forbidden(new_student, new_mentor, admin, method, path, body, allowed):
    actors = {S: new_student(), M: new_mentor(), A: admin}
    for role, actor in actors.items():
        if path == "/auth/logout":  # use a throwaway session so we do not kill the fixture token
            actor.relogin()
        r = actor.api.req(method, path, json=body)
        if role in allowed:
            assert r.status_code not in (401, 403), f"{role} should be allowed on {method} {path}, got {r.status_code} {r.text[:200]}"
        else:
            assert r.status_code == 403, f"{role} should be forbidden on {method} {path}, got {r.status_code} {r.text[:200]}"
    if path == "/auth/logout":
        admin.relogin()


def test_student_cannot_use_mentor_actions_on_real_request(new_student, new_mentor, send_request):
    s, m = new_student(), new_mentor()
    req = send_request(s, m)
    assert s.api.post(f"/requests/{req['id']}/accept").status_code == 403
    assert s.api.post(f"/requests/{req['id']}/reject", {}).status_code == 403
    assert m.api.post(f"/requests/{req['id']}/cancel").status_code == 403
