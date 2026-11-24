"""M3.8: Request and relationship state transitions, expiry, closure"""
from datetime import date, timedelta
import os, pytest
import pytest
from conftest import MSG, make_mentor, new_relationship, new_request, rec, register

def test_reject_flow(api, mentor2, areas):
    s = register(api, "STUDENT")
    rid = new_request(api, s, mentor2, areas[0]).json()["id"]
    rec("reject student", "POST /requests/{id}/reject", "student", 403, api.call("POST", f"/requests/{rid}/reject", s["token"], json={}))
    rec("reject reason too long", "POST /requests/{id}/reject", "501", 422, api.call("POST", f"/requests/{rid}/reject", mentor2["token"], json={"reason": "x" * 501}))
    r = rec("reject", "POST /requests/{id}/reject", "reason", 200, api.call("POST", f"/requests/{rid}/reject", mentor2["token"], json={"reason": "Busy"}))
    assert r.json()["status"] == "REJECTED" and r.json()["reject_reason"] == "Busy"
    rec("accept rejected", "POST /requests/{id}/accept", "rejected", 409, api.call("POST", f"/requests/{rid}/accept", mentor2["token"]))
    # after rejection the student may send a new request
    rec("re-request after reject", "POST /requests", "-", 201, new_request(api, s, mentor2, areas[0]))


def test_cancel_flow(api, mentor2, areas):
    s, other = register(api, "STUDENT"), register(api, "STUDENT")
    rid = new_request(api, s, mentor2, areas[0]).json()["id"]
    rec("cancel by mentor", "POST /requests/{id}/cancel", "mentor", 403, api.call("POST", f"/requests/{rid}/cancel", mentor2["token"]))
    rec("cancel other student", "POST /requests/{id}/cancel", "stranger", (403, 404), api.call("POST", f"/requests/{rid}/cancel", other["token"]))
    r = rec("cancel", "POST /requests/{id}/cancel", "owner", 200, api.call("POST", f"/requests/{rid}/cancel", s["token"]))
    assert r.json()["status"] == "CANCELLED"
    rec("cancel twice", "POST /requests/{id}/cancel", "again", 409, api.call("POST", f"/requests/{rid}/cancel", s["token"]))


def test_expiry_after_48h(api, mentor2, areas):
    import psycopg
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    s = register(api, "STUDENT")
    rid = new_request(api, s, mentor2, areas[0]).json()["id"]
    with psycopg.connect(url.replace("+psycopg", "")) as c:
        c.execute("UPDATE mentoring_requests SET expires_at = now() - interval '1 hour' WHERE request_id=%s", (rid,))
    rec("accept expired", "POST /requests/{id}/accept", "expired", 409, api.call("POST", f"/requests/{rid}/accept", mentor2["token"]))
    assert api.call("GET", f"/requests/{rid}", s["token"]).json()["status"] == "EXPIRED"


def test_relationship_lifecycle(api, admin, areas):
    m = make_mentor(api, admin, [areas[0]], max_mentees=1)
    s = register(api, "STUDENT")
    rel, _ = new_relationship(api, s, m, areas[0])
    st = lambda who, v: api.call("PATCH", f"/relationships/{rel}/status", who["token"], json={"status": v})
    rec("rel list student", "GET /relationships", "-", 200, api.call("GET", "/relationships", s["token"]))
    rec("rel get", "GET /relationships/{id}", rel, 200, api.call("GET", f"/relationships/{rel}", m["token"]))
    rec("rel get stranger", "GET /relationships/{id}", "other", 404, api.call("GET", f"/relationships/{rel}", register(api, "STUDENT")["token"]))
    rec("rel get missing", "GET /relationships/{id}", 99999999, 404, api.call("GET", "/relationships/99999999", s["token"]))
    rec("rel bad status filter", "GET /relationships?status=X", "X", 422, api.call("GET", "/relationships", s["token"], params={"status": "X"}))
    rec("pause", "PATCH /relationships/{id}/status", "PAUSED", 200, st(s, "PAUSED"))
    # paused still occupies the slot
    assert api.call("GET", f"/mentors/{m['id']}", register(api, "STUDENT")["token"]).json()["available"] is False
    rec("same status", "PATCH /relationships/{id}/status", "PAUSED again", 409, st(s, "PAUSED"))
    rec("resume", "PATCH /relationships/{id}/status", "ACTIVE", 200, st(m, "ACTIVE"))
    rec("student closes", "PATCH /relationships/{id}/status", "CLOSED by student", 403, st(s, "CLOSED"))
    rec("bad status value", "PATCH /relationships/{id}/status", "DONE", 422, st(s, "DONE"))
    rec("complete", "PATCH /relationships/{id}/status", "COMPLETED", 200, st(s, "COMPLETED"))
    assert api.call("GET", f"/relationships/{rel}", s["token"]).json()["ended_at"] is not None
    rec("reopen completed", "PATCH /relationships/{id}/status", "ACTIVE", 409, st(m, "ACTIVE"))
    # slot freed
    assert api.call("GET", f"/mentors/{m['id']}", s["token"]).json()["available"] is True


def test_mentor_can_close(api, mentor2, areas):
    s = register(api, "STUDENT")
    rel, _ = new_relationship(api, s, mentor2, areas[0])
    r = rec("mentor closes", "PATCH /relationships/{id}/status", "CLOSED", 200, api.call("PATCH", f"/relationships/{rel}/status", mentor2["token"], json={"status": "CLOSED"}))
    assert r.json()["status"] == "CLOSED"


@pytest.fixture
def rel(api, admin, areas):
    m = make_mentor(api, admin, [areas[0]], max_mentees=20)  # fresh mentor each time
    s = register(api, "STUDENT")
    rid, _ = new_relationship(api, s, m, areas[0])
    return {"id": rid, "s": s, "m": m}


def test_closed_relationship_blocks_goal_activity_but_not_feedback(api, rel):
    api.call("PATCH", f"/relationships/{rel['id']}/status", rel["m"]["token"], json={"status": "CLOSED"})
    rec("goal on closed", "POST goals", "closed", 409, api.call("POST", f"/relationships/{rel['id']}/goals", rel["s"]["token"], json={"title": "a"}))
    rec("activity on closed", "POST activities", "closed", 409, api.call("POST", f"/relationships/{rel['id']}/activities", rel["s"]["token"], json={"activity_type": "OTHER", "notes": "n"}))
    rec("feedback on closed", "POST feedback", "closed", 200, api.call("POST", f"/relationships/{rel['id']}/feedback", rel["s"]["token"], json={"rating": 5}))
