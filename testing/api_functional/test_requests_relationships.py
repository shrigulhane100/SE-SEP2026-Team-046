"""M3.5: Mentoring requests and relationships (creation, listing, acceptance)"""
import os, pytest
from conftest import MSG, make_mentor, new_relationship, new_request, rec, register

def test_create_request_ok(api, student1, mentor2, areas):
    r = rec("create request", "POST /requests", "valid", 201, new_request(api, student1, mentor2, areas[0]))
    j = r.json()
    assert j["status"] == "PENDING" and j["student_id"] == student1["id"] and j["mentor_id"] == mentor2["id"]
    assert j["hours_left"] in (47, 48)


def test_duplicate_pending_blocked(api, areas, mentor2):
    s = register(api, "STUDENT")
    assert new_request(api, s, mentor2, areas[0]).status_code == 201
    rec("dup pending", "POST /requests", "same pair", 409, new_request(api, s, mentor2, areas[0]))


@pytest.mark.parametrize("label,patch,code", [
    ("message <20 chars", {"message": "too short"}, 422),
    ("message >2000", {"message": "x" * 2001}, 422),
    ("objective >500", {"objective": "x" * 501}, 422),
    ("bad type", {"type": "FOREVER"}, 422),
    ("mentor_id string", {"mentor_id": "1"}, 422),
    ("mentor_id 0", {"mentor_id": 0}, 422),
    ("extra field", {"foo": 1}, 422),
    ("missing mentor 404", {"mentor_id": 99999999}, 404),
])
def test_create_request_validation(api, student2, mentor2, areas, label, patch, code):
    body = {"mentor_id": mentor2["id"], "area_id": areas[0], "message": MSG, "objective": "", "type": "ONE_TIME", **patch}
    rec(f"request {label}", "POST /requests", label, code, api.call("POST", "/requests", student2["token"], json=body))


def test_create_request_business_rules(api, student2, mentor1, mentor_unverified, mentor_closed, areas):
    rec("req unverified mentor", "POST /requests", "unverified", (404, 409), new_request(api, student2, mentor_unverified, areas[0]))
    rec("req not accepting", "POST /requests", "closed", 409, new_request(api, student2, mentor_closed, areas[0]))
    rec("req area not offered", "POST /requests", "mentor1 lacks area B", 422, new_request(api, student2, mentor1, areas[1]))
    rec("req unknown area", "POST /requests", 99999999, (404, 422), new_request(api, student2, mentor1, 99999999))


def test_create_request_rbac(api, mentor1, mentor2, admin, areas):
    rec("mentor creates req", "POST /requests", "mentor", 403, new_request(api, mentor1, mentor2, areas[0]))
    rec("admin creates req", "POST /requests", "admin", 403, new_request(api, admin, mentor2, areas[0]))
    rec("anon creates req", "POST /requests", "-", 401, api.call("POST", "/requests", json={}))


def test_full_capacity_blocks_request(api, admin, areas):
    m = make_mentor(api, admin, [areas[0]], max_mentees=1)
    new_relationship(api, register(api, "STUDENT"), m, areas[0])
    rec("req to full mentor", "POST /requests", "capacity", 409, new_request(api, register(api, "STUDENT"), m, areas[0]))


def test_list_and_get_requests(api, student1, mentor2, areas):
    rid = new_request(api, register(api, "STUDENT"), mentor2, areas[0]).json()["id"]
    r = rec("mentor inbox", "GET /requests", "mentor", 200, api.call("GET", "/requests", mentor2["token"]))
    assert rid in [x["id"] for x in r.json()]
    r = rec("inbox status filter", "GET /requests?status=PENDING", "-", 200, api.call("GET", "/requests", mentor2["token"], params={"status": "PENDING"}))
    assert all(x["status"] == "PENDING" for x in r.json())
    rec("bad status filter", "GET /requests?status=X", "X", 422, api.call("GET", "/requests", mentor2["token"], params={"status": "X"}))
    rec("get request mentor", "GET /requests/{id}", rid, 200, api.call("GET", f"/requests/{rid}", mentor2["token"]))
    rec("get request stranger", "GET /requests/{id}", "other student", 404, api.call("GET", f"/requests/{rid}", student1["token"]))
    rec("get request missing", "GET /requests/{id}", 99999999, 404, api.call("GET", "/requests/99999999", mentor2["token"]))
    rec("get request anon", "GET /requests/{id}", "-", 401, api.call("GET", f"/requests/{rid}"))


def test_accept_flow_and_permissions(api, mentor2, mentor1, areas):
    s = register(api, "STUDENT")
    rid = new_request(api, s, mentor2, areas[0]).json()["id"]
    rec("student accepts", "POST /requests/{id}/accept", "student", 403, api.call("POST", f"/requests/{rid}/accept", s["token"]))
    rec("other mentor accepts", "POST /requests/{id}/accept", "mentor1", (403, 404), api.call("POST", f"/requests/{rid}/accept", mentor1["token"]))
    r = rec("accept", "POST /requests/{id}/accept", "owner mentor", 200, api.call("POST", f"/requests/{rid}/accept", mentor2["token"]))
    assert r.json()["request"]["status"] == "ACCEPTED" and r.json()["relationship"]["status"] == "ACTIVE"
    rec("accept twice", "POST /requests/{id}/accept", "again", 409, api.call("POST", f"/requests/{rid}/accept", mentor2["token"]))
    rec("reject accepted", "POST /requests/{id}/reject", "accepted", 409, api.call("POST", f"/requests/{rid}/reject", mentor2["token"], json={}))
    rec("cancel accepted", "POST /requests/{id}/cancel", "accepted", 409, api.call("POST", f"/requests/{rid}/cancel", s["token"]))
    rec("accept missing", "POST /requests/{id}/accept", 99999999, 404, api.call("POST", "/requests/99999999/accept", mentor2["token"]))
