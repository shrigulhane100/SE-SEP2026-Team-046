"""M3.4: Mentor discovery and matching APIs"""
import pytest
from conftest import make_mentor, rec

def test_public_list_hides_unverified(api, mentor1, mentor_unverified):
    r = rec("public mentors", "GET /public/mentors", "anon", 200, api.call("GET", "/public/mentors", params={"limit": 100}))
    ids = [m["id"] for m in r.json()]
    assert mentor_unverified["id"] not in ids
    assert all(m["match"] is None for m in r.json())


def test_student_list_ok_and_rbac(api, student1, mentor1, mentor2, mentor_unverified, admin):
    r = rec("mentors student", "GET /mentors", "student", 200, api.call("GET", "/mentors", student1["token"], params={"limit": 100}))
    ids = [m["id"] for m in r.json()]
    assert mentor2["id"] in ids and mentor_unverified["id"] not in ids
    rec("mentors anon", "GET /mentors", "-", 401, api.call("GET", "/mentors"))
    rec("mentors mentor", "GET /mentors", "mentor", 403, api.call("GET", "/mentors", mentor1["token"]))
    rec("mentors admin", "GET /mentors", "admin", 403, api.call("GET", "/mentors", admin["token"]))


def test_match_score_for_student_with_areas(api, student1, mentor1):
    r = api.call("GET", "/mentors", student1["token"], params={"limit": 100}).json()
    m = next(x for x in r if x["id"] == mentor1["id"])
    assert m["match"] == 100  # student prefers area A, mentor1 offers A


def test_filters(api, student1, areas, mentor1, mentor2):
    g = lambda **p: api.call("GET", "/mentors", student1["token"], params={"limit": 100, **p})
    r = rec("filter area", "GET /mentors?area_id", areas[1], 200, g(area_id=areas[1]))
    assert mentor2["id"] in [m["id"] for m in r.json()] and mentor1["id"] not in [m["id"] for m in r.json()]
    r = g(q="TestCo"); assert r.status_code == 200 and len(r.json()) >= 1
    r = g(min_experience=60); assert r.status_code == 200 and r.json() == []
    r = g(industry="Information Technology"); assert len(r.json()) >= 1
    r = g(mentor_type="Industry Professional"); assert len(r.json()) >= 1
    r = g(q="zzzz-no-match-" * 3); assert r.json() == []
    r = g(availability="available"); assert all(m["available"] for m in r.json())


def test_sort_experience(api, student1):
    r = rec("sort experience", "GET /mentors?sort=experience", "-", 200, api.call("GET", "/mentors", student1["token"], params={"sort": "experience", "limit": 100}))
    ys = [m["experience_years"] for m in r.json()]
    assert ys == sorted(ys, reverse=True)


@pytest.mark.parametrize("label,params", [
    ("limit 0", {"limit": 0}), ("limit 101", {"limit": 101}), ("offset -1", {"offset": -1}),
    ("bad sort", {"sort": "random"}), ("bad availability", {"availability": "maybe"}),
    ("min_exp 61", {"min_experience": 61}), ("area_id 0", {"area_id": 0}),
    ("unknown param", {"foo": "bar"}), ("q 101 chars", {"q": "a" * 101}),
])
def test_filter_validation(api, student1, label, params):
    rec(f"discovery {label}", "GET /mentors", params, 422, api.call("GET", "/mentors", student1["token"], params=params))


def test_mentor_detail(api, student1, mentor2, mentor_unverified):
    r = rec("mentor detail", "GET /mentors/{id}", mentor2["id"], 200, api.call("GET", f"/mentors/{mentor2['id']}", student1["token"]))
    assert r.json()["id"] == mentor2["id"]
    rec("mentor detail missing", "GET /mentors/{id}", 99999999, 404, api.call("GET", "/mentors/99999999", student1["token"]))
    rec("mentor detail unverified", "GET /mentors/{id}", "unverified", 404, api.call("GET", f"/mentors/{mentor_unverified['id']}", student1["token"]))
    rec("mentor detail id 0", "GET /mentors/{id}", 0, 422, api.call("GET", "/mentors/0", student1["token"]))
    rec("mentor detail anon", "GET /mentors/{id}", "-", 401, api.call("GET", f"/mentors/{mentor2['id']}"))


def test_availability_reflects_capacity(api, admin, areas, student1):
    from conftest import register, new_relationship
    m = make_mentor(api, admin, [areas[0]], max_mentees=1)
    new_relationship(api, register(api, "STUDENT"), m, areas[0])
    d = api.call("GET", f"/mentors/{m['id']}", student1["token"]).json()
    assert d["available"] is False and d["active_mentees"] == 1


def test_verification_flow(api, admin, areas, student1, mentor1):
    m = make_mentor(api, admin, [areas[0]], verified=False)
    rec("verif list", "GET /admin/mentor-verifications", "admin", 200, api.call("GET", "/admin/mentor-verifications", admin["token"]))
    rec("verif list student", "GET /admin/mentor-verifications", "student", 403, api.call("GET", "/admin/mentor-verifications", student1["token"]))
    rec("verify student role", "POST /admin/mentors/{id}/verify", "student", 403, api.call("POST", f"/admin/mentors/{m['id']}/verify", student1["token"], json={"approve": True}))
    rec("verify bad body", "POST /admin/mentors/{id}/verify", "approve='yes'", 422, api.call("POST", f"/admin/mentors/{m['id']}/verify", admin["token"], json={"approve": "yes"}))
    rec("verify missing mentor", "POST /admin/mentors/{id}/verify", 99999999, 404, api.call("POST", "/admin/mentors/99999999/verify", admin["token"], json={"approve": True}))
    rec("verify student id", "POST /admin/mentors/{id}/verify", "student id", 404, api.call("POST", f"/admin/mentors/{student1['id']}/verify", admin["token"], json={"approve": True}))
    rec("approve", "POST /admin/mentors/{id}/verify", True, 200, api.call("POST", f"/admin/mentors/{m['id']}/verify", admin["token"], json={"approve": True}))
    assert m["id"] in [x["id"] for x in api.call("GET", "/public/mentors", params={"limit": 100}).json()]
    rec("reject", "POST /admin/mentors/{id}/verify", False, 200, api.call("POST", f"/admin/mentors/{m['id']}/verify", admin["token"], json={"approve": False}))
    assert m["id"] not in [x["id"] for x in api.call("GET", "/public/mentors", params={"limit": 100}).json()]
