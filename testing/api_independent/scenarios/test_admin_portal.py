"""Admin portal: user management, guidance areas, mentor verification (all admin staff types)."""
import pytest
from .conftest import RUN
from .helpers import fail, ok


def test_user_list_filters_and_search(admin, new_student, new_mentor):
    s, m = new_student(), new_mentor()
    users = ok(admin.api.get("/admin/users"))
    ids = {u["id"] for u in users}
    assert {s.id, m.id, admin.id} <= ids
    assert all("password" not in u and "password_hash" not in u for u in users)
    assert {u["role"] for u in ok(admin.api.get("/admin/users", params={"role": "STUDENT"}))} == {"STUDENT"}
    assert {u["role"] for u in ok(admin.api.get("/admin/users", params={"role": "MENTOR"}))} == {"MENTOR"}
    assert {u["role"] for u in ok(admin.api.get("/admin/users", params={"role": "ADMIN"}))} == {"ADMIN"}
    found = ok(admin.api.get("/admin/users", params={"q": s.email.upper()}))
    assert [u["id"] for u in found] == [s.id]
    assert ok(admin.api.get("/admin/users", params={"q": f"no-such-user-{RUN}"})) == []
    assert any(u["verification_status"] == "VERIFIED" for u in ok(admin.api.get("/admin/users", params={"q": m.email})))
    fail(admin.api.get("/admin/users", params={"role": "NOPE"}), 422)
    # SQL wildcard characters are treated literally
    assert ok(admin.api.get("/admin/users", params={"q": "%"})) == []


def test_every_admin_staff_type_has_full_admin_access(make_admin):
    for staff in ("PLACEMENT_TEAM", "PROGRAMME_ADMIN", "FACULTY_TA"):
        a = make_admin(staff)
        ok(a.api.get("/admin/users")); ok(a.api.get("/admin/guidance-areas")); ok(a.api.get("/admin/mentor-verifications"))


def test_guidance_area_crud(admin, anon):
    name = f"CRUD Area {RUN}"
    a = ok(admin.api.post("/admin/guidance-areas", {"name": name, "category": "Test"}), 201)
    assert a["is_active"] is True and a["name"] == name and a["category"] == "Test"
    fail(admin.api.post("/admin/guidance-areas", {"name": name.upper()}), 409, "already exists")   # case-insensitive unique
    for bad in ({"name": ""}, {"name": " "}, {}, {"name": "x", "bogus": 1}, {"name": "x" * 151}):
        fail(admin.api.post("/admin/guidance-areas", bad), 422)
    renamed = ok(admin.api.patch(f"/admin/guidance-areas/{a['id']}", {"name": name + " v2", "category": "Changed"}))
    assert renamed["name"].endswith("v2") and renamed["category"] == "Changed"
    # deactivate hides it from the public list but keeps it in the admin list
    ok(admin.api.patch(f"/admin/guidance-areas/{a['id']}", {"is_active": False}))
    assert a["id"] not in {x["id"] for x in ok(anon.get("/guidance-areas"))}
    adm = {x["id"]: x for x in ok(admin.api.get("/admin/guidance-areas"))}
    assert adm[a["id"]]["is_active"] is False and {"mentors", "requests"} <= set(adm[a["id"]])
    ok(admin.api.patch(f"/admin/guidance-areas/{a['id']}", {"is_active": True}))
    assert a["id"] in {x["id"] for x in ok(anon.get("/guidance-areas"))}
    fail(admin.api.patch("/admin/guidance-areas/999999", {"name": "zzz"}), 404)
    fail(admin.api.patch(f"/admin/guidance-areas/{a['id']}", {"name": None}), 422)
    fail(admin.api.patch(f"/admin/guidance-areas/{a['id']}", {"is_active": "yes"}), 422)


def test_guidance_area_counts_reflect_usage(admin, areas, new_mentor, new_student, send_request):
    area = ok(admin.api.post("/admin/guidance-areas", {"name": f"Counted {RUN}"}), 201)
    before = {x["id"]: x for x in ok(admin.api.get("/admin/guidance-areas"))}[area["id"]]
    m, s = new_mentor(area_ids=[area["id"]]), new_student(area_ids=[area["id"]])
    send_request(s, m, area_id=area["id"])
    after = {x["id"]: x for x in ok(admin.api.get("/admin/guidance-areas"))}[area["id"]]
    assert after["mentors"] == before["mentors"] + 1 and after["requests"] == before["requests"] + 1


def test_mentor_verification_flow(admin, new_mentor, new_student, anon):
    m = new_mentor(verify=False)
    queue = {x["id"]: x for x in ok(admin.api.get("/admin/mentor-verifications"))}
    assert queue[m.id]["verification_status"] == "PENDING"
    assert m.id not in {x["id"] for x in ok(anon.get("/public/mentors", params={"q": m.name}))}
    ok(admin.api.post(f"/admin/mentors/{m.id}/verify", {"approve": True}))
    assert ok(m.api.get("/profile/me"))["profile"]["verification_status"] == "VERIFIED"
    assert m.id in {x["id"] for x in ok(anon.get("/public/mentors", params={"q": m.name}))}
    ok(admin.api.post(f"/admin/mentors/{m.id}/verify", {"approve": False}))            # revoke / reject
    assert ok(m.api.get("/profile/me"))["profile"]["verification_status"] == "REJECTED"
    assert m.id not in {x["id"] for x in ok(anon.get("/public/mentors", params={"q": m.name}))}
    fail(new_student().api.get(f"/mentors/{m.id}"), 404)
    fail(admin.api.post("/admin/mentors/999999/verify", {"approve": True}), 404)
    fail(admin.api.post(f"/admin/mentors/{m.id}/verify", {}), 422)
    fail(admin.api.post(f"/admin/mentors/{m.id}/verify", {"approve": "maybe"}), 422)
