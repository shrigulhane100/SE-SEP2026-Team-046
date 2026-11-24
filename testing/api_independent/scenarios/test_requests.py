"""Mentoring request lifecycle: student sends/cancels, mentor accepts/rejects, edge cases."""
import pytest
from .conftest import RUN
from .helpers import MSG, fail, ok


def test_student_sends_request_and_both_sides_see_it(new_student, new_mentor, send_request, areas):
    s, m = new_student(), new_mentor()
    req = send_request(s, m, type="ONE_TIME", objective="Crack interviews")
    assert req["status"] == "PENDING" and req["type"] == "ONE_TIME" and req["student"]["id"] == s.id and req["mentor"]["id"] == m.id
    assert req["relationship_id"] is None and 46 <= req["hours_left"] <= 48 and req["area"] == areas[0]["name"] and req["responded_at"] is None
    assert [r["id"] for r in ok(s.api.get("/requests"))] == [req["id"]]
    assert [r["id"] for r in ok(m.api.get("/requests"))] == [req["id"]]
    assert ok(s.api.get(f"/requests/{req['id']}"))["id"] == req["id"] and ok(m.api.get(f"/requests/{req['id']}"))["message"] == MSG


@pytest.mark.parametrize("rtype", ["ONE_TIME", "LONG_TERM"])
def test_both_mentoring_types(new_student, new_mentor, send_request, rtype):
    assert send_request(new_student(), new_mentor(), type=rtype)["type"] == rtype


def test_request_validation(new_student, new_mentor, areas):
    s, m = new_student(), new_mentor(area_ids=[areas[0]["id"]])
    good = {"mentor_id": m.id, "area_id": areas[0]["id"], "message": MSG, "type": "LONG_TERM"}
    for bad in ({"message": "too short"}, {"message": "x" * 2001}, {"type": "WEEKLY"}, {"objective": "o" * 501}, {"mentor_id": "1"}, {"mentor_id": 0}, {"area_id": -1}, {"extra": "field"}):
        fail(s.api.post("/requests", {**good, **bad}), 422)
    fail(s.api.post("/requests", {k: v for k, v in good.items() if k != "type"}), 422)
    fail(s.api.post("/requests", {**good, "mentor_id": 999999}), 404, "mentor not found")
    fail(s.api.post("/requests", {**good, "mentor_id": s.id}), 404)
    fail(s.api.post("/requests", {**good, "area_id": areas[2]["id"]}), 422, "does not offer")      # area the mentor does not offer
    fail(s.api.post("/requests", {**good, "area_id": 999999}), 422)


def test_unverified_or_not_accepting_mentor_blocked(new_student, new_mentor, send_request):
    s = new_student()
    fail(s.api.post("/requests", {"mentor_id": new_mentor(verify=False).id, "area_id": 1, "message": MSG, "type": "ONE_TIME"}), 409, "not verified")
    m = new_mentor(is_accepting=False)
    fail(s.api.post("/requests", {"mentor_id": m.id, "area_id": ok(m.api.get("/profile/me"))["area_ids"][0], "message": MSG, "type": "ONE_TIME"}), 409, "not accepting")


def test_duplicate_pending_blocked_but_allowed_after_resolution(new_student, new_mentor, send_request):
    s, m = new_student(), new_mentor(max_mentees=5)
    r1 = send_request(s, m)
    fail(s.api.post("/requests", {"mentor_id": m.id, "area_id": r1["area_id"], "message": MSG, "type": "LONG_TERM"}), 409, "already have a pending")
    ok(s.api.post(f"/requests/{r1['id']}/cancel"))
    assert send_request(s, m)["id"] != r1["id"]                      # fine once the first is cancelled
    other = new_student()
    assert send_request(other, m)                                    # other students are unaffected


def test_mentor_accepts_request_creates_relationship(new_student, new_mentor, send_request):
    s, m = new_student(), new_mentor()
    req = send_request(s, m)
    body = ok(m.api.post(f"/requests/{req['id']}/accept"))
    assert body["request"]["status"] == "ACCEPTED" and body["request"]["responded_at"] and body["request"]["hours_left"] is None
    rel = body["relationship"]
    assert rel["status"] == "ACTIVE" and rel["request_id"] == req["id"] and rel["type"] == req["type"] and rel["goals"] == [] and rel["progress"] == 0
    assert ok(s.api.get(f"/requests/{req['id']}"))["relationship_id"] == rel["id"]
    assert ok(s.api.get(f"/relationships/{rel['id']}"))["student"]["id"] == s.id
    fail(m.api.post(f"/requests/{req['id']}/accept"), 409, "already accepted")        # no second relationship
    fail(m.api.post(f"/requests/{req['id']}/reject", {}), 409)
    fail(s.api.post(f"/requests/{req['id']}/cancel"), 409)
    assert len(ok(m.api.get("/relationships"))) == 1


def new_req_id(mentor, student, send_request):
    return send_request(student, mentor)["id"]


def test_mentor_rejects_with_and_without_reason(new_student, new_mentor, send_request):
    m = new_mentor(max_mentees=5)
    s1, s2 = new_student(), new_student()
    r1, r2 = send_request(s1, m), send_request(s2, m)
    out = ok(m.api.post(f"/requests/{r1['id']}/reject", {"reason": "Not a fit right now"}))
    assert out["status"] == "REJECTED" and out["reject_reason"] == "Not a fit right now" and out["relationship_id"] is None
    assert ok(m.api.post(f"/requests/{r2['id']}/reject", {}))["reject_reason"] in (None, "")
    assert ok(s1.api.get(f"/requests/{r1['id']}"))["status"] == "REJECTED"
    fail(m.api.post(f"/requests/{r1['id']}/accept"), 409, "already rejected")
    fail(m.api.post(f"/requests/{new_req_id(m, s1, send_request)}/reject", {"reason": "r" * 501}), 422)
    assert ok(m.api.get("/relationships")) == []


def test_student_cancels_pending_request(new_student, new_mentor, send_request):
    s, m = new_student(), new_mentor()
    req = send_request(s, m)
    assert ok(s.api.post(f"/requests/{req['id']}/cancel"))["status"] == "CANCELLED"
    fail(m.api.post(f"/requests/{req['id']}/accept"), 409, "cancelled")
    fail(s.api.post(f"/requests/{req['id']}/cancel"), 409)


def test_list_filters_ordering_and_isolation(new_student, new_mentor, send_request):
    s, m = new_student(), new_mentor(max_mentees=5)
    other_student, other_mentor = new_student(), new_mentor()
    r1, r2, r3 = send_request(s, m), send_request(new_student(), m), send_request(new_student(), m)
    ok(m.api.post(f"/requests/{r1['id']}/accept")); ok(m.api.post(f"/requests/{r2['id']}/reject", {}))
    inbox = ok(m.api.get("/requests"))
    assert [r["id"] for r in inbox] == [r3["id"], r2["id"], r1["id"]]                  # newest first
    for status, want in (("PENDING", [r3["id"]]), ("REJECTED", [r2["id"]]), ("ACCEPTED", [r1["id"]]), ("EXPIRED", []), ("CANCELLED", [])):
        assert [r["id"] for r in ok(m.api.get("/requests", params={"status": status}))] == want
    fail(m.api.get("/requests", params={"status": "BOGUS"}), 422)
    assert ok(other_student.api.get("/requests")) == [] and ok(other_mentor.api.get("/requests")) == []


def test_non_participants_cannot_see_or_act_on_a_request(new_student, new_mentor, send_request):
    s, m, intruder_s, intruder_m = new_student(), new_mentor(), new_student(), new_mentor()
    req = send_request(s, m)
    fail(intruder_s.api.get(f"/requests/{req['id']}"), 404)
    fail(intruder_m.api.get(f"/requests/{req['id']}"), 404)
    fail(intruder_m.api.post(f"/requests/{req['id']}/accept"), 404)
    fail(intruder_m.api.post(f"/requests/{req['id']}/reject", {}), 404)
    fail(intruder_s.api.post(f"/requests/{req['id']}/cancel"), 404)
    fail(m.api.get("/requests/999999"), 404)
    fail(m.api.get("/requests/abc"), 422)


def test_request_expires_after_48_hours(new_student, new_mentor, send_request, expire_request):
    s, m = new_student(), new_mentor()
    req = send_request(s, m)
    expire_request(req["id"])
    fail(m.api.post(f"/requests/{req['id']}/accept"), 409, "expired")
    got = ok(s.api.get(f"/requests/{req['id']}"))
    assert got["status"] == "EXPIRED" and got["hours_left"] is None
    assert [r["id"] for r in ok(m.api.get("/requests", params={"status": "EXPIRED"}))] == [req["id"]]
    assert ok(m.api.get("/relationships")) == []
    send_request(s, m)                                                       # student can try again after expiry
