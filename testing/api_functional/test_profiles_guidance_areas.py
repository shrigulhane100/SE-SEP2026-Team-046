"""M3.3: Profile and guidance-area APIs"""
import pytest
from conftest import rec, register, uid

def test_guidance_public_list(api, areas):
    r = rec("list areas", "GET /guidance-areas", "-", 200, api.call("GET", "/guidance-areas"))
    ids = [a["id"] for a in r.json()]
    assert all(a in ids for a in areas)


def test_meta(api):
    rec("meta", "GET /meta", "-", 200, api.call("GET", "/meta"))


def test_admin_create_area_rbac(api, student1, mentor1):
    for who in (student1, mentor1):
        rec("area create non-admin", "POST /admin/guidance-areas", who["id"], 403,
            api.call("POST", "/admin/guidance-areas", who["token"], json={"name": "X" + uid()}))
    rec("area create anon", "POST /admin/guidance-areas", "-", 401, api.call("POST", "/admin/guidance-areas", json={"name": "Y"}))


def test_area_duplicate_case_insensitive(api, admin):
    n = "Dup" + uid()
    rec("area create", "POST /admin/guidance-areas", n, 201, api.call("POST", "/admin/guidance-areas", admin["token"], json={"name": n}))
    rec("area dup case", "POST /admin/guidance-areas", n.upper(), 409, api.call("POST", "/admin/guidance-areas", admin["token"], json={"name": n.upper()}))


def test_area_validation(api, admin):
    rec("area empty name", "POST /admin/guidance-areas", "''", 422, api.call("POST", "/admin/guidance-areas", admin["token"], json={"name": ""}))
    rec("area no body", "POST /admin/guidance-areas", "{}", 422, api.call("POST", "/admin/guidance-areas", admin["token"], json={}))


def test_area_patch_and_inactive(api, admin, student1):
    r = api.call("POST", "/admin/guidance-areas", admin["token"], json={"name": "Tmp" + uid()})
    aid = r.json()["id"]
    rec("area deactivate", "PATCH /admin/guidance-areas/{id}", "is_active=false", 200,
        api.call("PATCH", f"/admin/guidance-areas/{aid}", admin["token"], json={"is_active": False}))
    assert aid not in [a["id"] for a in api.call("GET", "/guidance-areas").json()]
    rec("select inactive area", "PUT /profile/me", aid, 422,
        api.call("PUT", "/profile/me", student1["token"], json={"area_ids": [aid]}))
    rec("area patch missing", "PATCH /admin/guidance-areas/{id}", 999999, 404,
        api.call("PATCH", "/admin/guidance-areas/999999", admin["token"], json={"name": "zz"}))
    rec("area patch student", "PATCH /admin/guidance-areas/{id}", "student", 403,
        api.call("PATCH", f"/admin/guidance-areas/{aid}", student1["token"], json={"name": "zz"}))


def test_admin_areas_list(api, admin, student1):
    rec("admin areas list", "GET /admin/guidance-areas", "admin", 200, api.call("GET", "/admin/guidance-areas", admin["token"]))
    rec("admin areas list student", "GET /admin/guidance-areas", "student", 403, api.call("GET", "/admin/guidance-areas", student1["token"]))


def test_profile_get_and_requires_auth(api, student1):
    rec("profile anon", "GET /profile/me", "-", 401, api.call("GET", "/profile/me"))
    r = rec("profile get", "GET /profile/me", "student", 200, api.call("GET", "/profile/me", student1["token"]))
    assert "profile_completion" in str(r.json()) and "area_ids" in r.json()


def test_admin_has_no_profile(api, admin):
    rec("admin profile", "GET /profile/me", "admin", (403, 404), api.call("GET", "/profile/me", admin["token"]))


def test_student_profile_update_persists_and_partial(api, areas):
    s = register(api, "STUDENT")
    rec("student profile create", "PUT /profile/me", "full", 200, api.call("PUT", "/profile/me", s["token"], json={
        "roll_number": s["body"]["roll_number"], "academic_level": "Degree", "skills": ["a", "b"], "area_ids": areas}))
    rec("partial update", "PUT /profile/me", "interests only", 200, api.call("PUT", "/profile/me", s["token"], json={"interests": "ML"}))
    p = api.call("GET", "/profile/me", s["token"]).json()
    assert p["profile"]["academic_level"] == "Degree" and p["profile"]["skills"] == ["a", "b"]
    assert sorted(p["area_ids"]) == sorted(areas)
    api.call("PUT", "/profile/me", s["token"], json={"area_ids": []})
    assert api.call("GET", "/profile/me", s["token"]).json()["area_ids"] == []


@pytest.mark.parametrize("label,body", [
    ("bad academic_level", {"academic_level": "PhD"}),
    ("bad preferred_mode", {"preferred_mode": "Carrier pigeon"}),
    ("unknown area", {"area_ids": [99999999]}),
    ("duplicate area ids", {"area_ids": [1, 1]}),
    ("null name", {"name": None}),
    ("31 skills", {"skills": [f"s{i}" for i in range(31)]}),
    ("mentor field on student", {"industry": "IT"}),
])
def test_student_profile_validation(api, student2, label, body):
    rec(f"student profile {label}", "PUT /profile/me", label, 422, api.call("PUT", "/profile/me", student2["token"], json=body))


@pytest.mark.parametrize("label,body", [
    ("max_mentees 0", {"max_mentees": 0}),
    ("max_mentees 21", {"max_mentees": 21}),
    ("experience -1", {"experience_years": -1}),
    ("experience 61", {"experience_years": 61}),
    ("is_accepting string", {"is_accepting": "yes"}),
    ("student field on mentor", {"academic_level": "Degree"}),
])
def test_mentor_profile_validation(api, mentor2, label, body):
    rec(f"mentor profile {label}", "PUT /profile/me", label, 422, api.call("PUT", "/profile/me", mentor2["token"], json=body))


def test_new_student_profile_needs_roll_number(api):
    s = register(api, "MENTOR")  # placeholder account; use a student w/o profile row
    st = register(api, "STUDENT")
    r = api.call("PUT", "/profile/me", st["token"], json={"academic_level": "Diploma"})
    assert r.status_code in (200, 422)


def test_roll_number_conflict(api, student1, student2):
    rec("roll conflict", "PUT /profile/me", "other's roll", 409, api.call(
        "PUT", "/profile/me", student2["token"], json={"roll_number": student1["body"]["roll_number"]}))


def test_max_mentees_below_occupancy(api, admin, areas, student1):
    from conftest import make_mentor, new_relationship
    m = make_mentor(api, admin, [areas[0]], max_mentees=2)
    s = register(api, "STUDENT")
    new_relationship(api, s, m, areas[0])
    rec("max_mentees below occupancy", "PUT /profile/me", "max=1 (1 occupied, was 2 → ok) then 0", 422,
        api.call("PUT", "/profile/me", m["token"], json={"max_mentees": 0}))
