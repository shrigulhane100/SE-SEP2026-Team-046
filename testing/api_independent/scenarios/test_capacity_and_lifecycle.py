"""Mentor capacity rules and the relationship state machine (ACTIVE <-> PAUSED -> COMPLETED | CLOSED)."""
import pytest
from .helpers import fail, ok


def accept(m, req): return ok(m.api.post(f"/requests/{req['id']}/accept"))["relationship"]


def test_capacity_blocks_accept_and_new_requests_until_slot_freed(new_student, new_mentor, send_request):
    m = new_mentor(max_mentees=1)
    s1, s2, s3 = new_student(), new_student(), new_student()
    r1, r2 = send_request(s1, m), send_request(s2, m)                      # two pending while a slot is open
    rel = accept(m, r1)
    fail(m.api.post(f"/requests/{r2['id']}/accept"), 409, "capacity")      # full
    assert ok(m.api.get(f"/requests/{r2['id']}"))["status"] == "PENDING"  # failed accept leaves it pending
    d = ok(s3.api.get(f"/mentors/{m.id}"))
    assert d["active_mentees"] == 1 and d["available"] is False
    fail(s3.api.post("/requests", {"mentor_id": m.id, "area_id": r1["area_id"], "message": "Please can I have mentoring support?", "type": "ONE_TIME"}), 409, "full capacity")
    assert m.id not in [x["id"] for x in ok(s3.api.get("/mentors", params={"availability": "available", "q": m.name}))]
    ok(m.api.patch(f"/relationships/{rel['id']}/status", {"status": "COMPLETED"}))   # frees the slot
    assert ok(s3.api.get(f"/mentors/{m.id}"))["available"] is True
    assert accept(m, r2)["status"] == "ACTIVE"


def test_paused_relationship_still_occupies_a_slot_and_closing_frees_it(new_student, new_mentor, send_request):
    m = new_mentor(max_mentees=1)
    s1, s2 = new_student(), new_student()
    rel = accept(m, send_request(s1, m))
    ok(s1.api.patch(f"/relationships/{rel['id']}/status", {"status": "PAUSED"}))
    assert ok(s2.api.get(f"/mentors/{m.id}"))["available"] is False
    ok(m.api.patch(f"/relationships/{rel['id']}/status", {"status": "CLOSED"}))
    assert ok(s2.api.get(f"/mentors/{m.id}"))["available"] is True


def test_cannot_lower_max_mentees_below_current_occupancy(new_student, new_mentor, send_request):
    m = new_mentor(max_mentees=3)
    for _ in range(2):
        accept(m, send_request(new_student(), m))
    fail(m.api.put("/profile/me", {"max_mentees": 1}), 422, "below current occupancy")
    assert ok(m.api.put("/profile/me", {"max_mentees": 2}))["profile"]["max_mentees"] == 2


def test_mentor_can_stop_accepting_without_losing_existing_mentees(active_pair, new_student):
    s, m, req, rel = active_pair()
    ok(m.api.put("/profile/me", {"is_accepting": False}))
    assert ok(m.api.get(f"/relationships/{rel['id']}"))["status"] == "ACTIVE"
    fail(new_student().api.post("/requests", {"mentor_id": m.id, "area_id": req["area_id"], "message": "Can you mentor me please?", "type": "ONE_TIME"}), 409)


def test_status_transitions_for_student_and_mentor(active_pair):
    s, m, req, rel = active_pair()
    path = f"/relationships/{rel['id']}/status"
    assert rel["ended_at"] is None
    assert ok(s.api.patch(path, {"status": "PAUSED"}))["status"] == "PAUSED"           # student pauses
    fail(m.api.patch(path, {"status": "PAUSED"}), 409, "invalid")                      # same status
    assert ok(m.api.patch(path, {"status": "ACTIVE"}))["status"] == "ACTIVE"           # mentor resumes
    out = ok(s.api.patch(path, {"status": "COMPLETED"}))
    assert out["status"] == "COMPLETED" and out["ended_at"]
    for target in ("ACTIVE", "PAUSED", "CLOSED", "COMPLETED"):
        fail(m.api.patch(path, {"status": target}), 409, "invalid")                    # terminal state


def test_only_mentor_can_close(active_pair):
    s, m, req, rel = active_pair()
    path = f"/relationships/{rel['id']}/status"
    fail(s.api.patch(path, {"status": "CLOSED"}), 403, "only the mentor")
    out = ok(m.api.patch(path, {"status": "CLOSED"}))
    assert out["status"] == "CLOSED" and out["ended_at"]


@pytest.mark.parametrize("body", [{"status": "BOGUS"}, {}, {"status": "ACTIVE", "x": 1}, {"status": None}])
def test_status_update_validation(active_pair, body):
    s, m, req, rel = active_pair()
    fail(m.api.patch(f"/relationships/{rel['id']}/status", body), 422)


def test_relationship_visibility_and_filters(active_pair, new_student, new_mentor, admin):
    s, m, req, rel = active_pair()
    for who in (s, m):
        assert [r["id"] for r in ok(who.api.get("/relationships"))] == [rel["id"]]
        assert ok(who.api.get(f"/relationships/{rel['id']}"))["area"] == req["area"]
        assert [r["id"] for r in ok(who.api.get("/relationships", params={"status": "ACTIVE"}))] == [rel["id"]]
        assert ok(who.api.get("/relationships", params={"status": "PAUSED"})) == []
    for stranger in (new_student(), new_mentor()):
        fail(stranger.api.get(f"/relationships/{rel['id']}"), 404)
        fail(stranger.api.patch(f"/relationships/{rel['id']}/status", {"status": "PAUSED"}), 404)
        assert ok(stranger.api.get("/relationships")) == []
    assert admin.api.get(f"/relationships/{rel['id']}").status_code == 403           # admins never read private mentoring data
    fail(s.api.get("/relationships/999999"), 404)
    fail(s.api.get("/relationships", params={"status": "BOGUS"}), 422)
