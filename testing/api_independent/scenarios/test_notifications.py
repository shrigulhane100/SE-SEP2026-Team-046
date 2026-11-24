"""In-app notifications: right recipient, right type/reference, read state and ownership."""
from .helpers import fail, ok


def notes(actor): return ok(actor.api.get("/notifications"))
def types(actor): return [n["type"] for n in notes(actor)["items"]]


def test_new_user_has_no_notifications(new_student, new_mentor, admin):
    for a in (new_student(), new_mentor()):
        assert notes(a) == {"items": [], "unread": 0}
    assert isinstance(notes(admin)["items"], list)


def test_request_lifecycle_notifications(new_student, new_mentor, send_request):
    s, m = new_student(), new_mentor(max_mentees=5)
    req = send_request(s, m)
    n = notes(m)["items"][0]
    assert n["type"] == "NEW_REQUEST" and n["reference_type"] == "REQUEST" and n["reference_id"] == req["id"] and n["is_read"] is False and s.name in n["message"]
    assert types(s) == []
    rel = ok(m.api.post(f"/requests/{req['id']}/accept"))["relationship"]
    n = notes(s)["items"][0]
    assert n["type"] == "REQUEST_ACCEPTED" and n["reference_id"] == rel["id"] and n["reference_type"] == "RELATIONSHIP"


def test_rejection_and_cancellation_notify_the_other_side(new_student, new_mentor, send_request):
    s1, s2, m = new_student(), new_student(), new_mentor(max_mentees=5)
    r1, r2 = send_request(s1, m), send_request(s2, m)
    ok(m.api.post(f"/requests/{r1['id']}/reject", {}))
    assert "REQUEST_REJECTED" in types(s1)
    ok(s2.api.post(f"/requests/{r2['id']}/cancel"))
    assert "REQUEST_CANCELLED" in types(m)


def test_relationship_events_notify_the_counterpart_only(active_pair):
    s, m, req, rel = active_pair()
    base = f"/relationships/{rel['id']}"
    ok(m.api.post(f"{base}/goals", {"title": "G"}), 201)
    ok(m.api.post(f"{base}/activities", {"activity_type": "MEETING", "notes": "n"}), 201)
    ok(m.api.post(f"{base}/feedback", {"rating": 5}))
    ok(m.api.patch(f"{base}/status", {"status": "PAUSED"}))
    got = types(s)
    for t in ("GOAL_ADDED", "ACTIVITY_LOGGED", "FEEDBACK_RECEIVED", "RELATIONSHIP_UPDATED"):
        assert t in got, f"student missing {t}: {got}"
    assert not {"GOAL_ADDED", "ACTIVITY_LOGGED", "FEEDBACK_RECEIVED", "RELATIONSHIP_UPDATED"} & set(types(m))   # actor is not notified of own actions
    ok(s.api.patch(f"{base}/status", {"status": "ACTIVE"}))
    assert "RELATIONSHIP_UPDATED" in types(m)
    assert all(n["reference_type"] == "RELATIONSHIP" and n["reference_id"] == rel["id"] for n in notes(s)["items"] if n["type"] in ("GOAL_ADDED", "ACTIVITY_LOGGED"))


def test_feedback_edit_does_not_spam_notifications(active_pair):
    s, m, req, rel = active_pair()
    path = f"/relationships/{rel['id']}/feedback"
    ok(s.api.post(path, {"rating": 3})); ok(s.api.post(path, {"rating": 5}))
    assert types(m).count("FEEDBACK_RECEIVED") == 1


def test_mark_read_and_read_all(active_pair):
    s, m, req, rel = active_pair()
    for i in range(3):
        ok(m.api.post(f"/relationships/{rel['id']}/goals", {"title": f"G{i}"}), 201)
    data = notes(s)
    assert data["unread"] == len(data["items"]) >= 4
    first = data["items"][0]["id"]
    assert ok(s.api.post(f"/notifications/{first}/read")) == {"ok": True}
    after = notes(s)
    assert after["unread"] == data["unread"] - 1 and next(n for n in after["items"] if n["id"] == first)["is_read"] is True
    ok(s.api.post(f"/notifications/{first}/read"))                    # idempotent
    assert ok(s.api.post("/notifications/read-all")) == {"ok": True}
    assert notes(s)["unread"] == 0 and notes(m)["unread"] >= 0
    created = [n["created_at"] for n in after["items"]]
    assert created == sorted(created, reverse=True)                   # newest first


def test_notifications_are_private(active_pair, new_student):
    s, m, req, rel = active_pair()
    nid = notes(s)["items"][0]["id"]
    fail(m.api.post(f"/notifications/{nid}/read"), 404)
    fail(new_student().api.post(f"/notifications/{nid}/read"), 404)
    fail(s.api.post("/notifications/999999999/read"), 404)
    assert notes(s)["items"][0]["is_read"] is False                   # untouched by the failed attempts


def test_expiry_notifies_both_parties(new_student, new_mentor, send_request, expire_request):
    s, m = new_student(), new_mentor()
    req = send_request(s, m)
    expire_request(req["id"])
    ok(s.api.get("/requests"))
    assert "REQUEST_EXPIRED" in types(s) and "REQUEST_EXPIRED" in types(m)
    ok(s.api.get("/requests"))                                          # no duplicates on repeat
    assert types(s).count("REQUEST_EXPIRED") == 1
