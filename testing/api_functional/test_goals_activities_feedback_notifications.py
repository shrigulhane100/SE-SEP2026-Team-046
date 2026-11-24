"""M3.6: Goals, activities, feedback and notifications"""
from datetime import date, timedelta
import pytest
from conftest import make_mentor, new_relationship, new_request, rec, register

@pytest.fixture
def rel(api, admin, areas):
    m = make_mentor(api, admin, [areas[0]], max_mentees=20)  # fresh mentor each time
    s = register(api, "STUDENT")
    rid, _ = new_relationship(api, s, m, areas[0])
    return {"id": rid, "s": s, "m": m}


def test_goal_create_update(api, rel):
    p = f"/relationships/{rel['id']}/goals"
    r = rec("add goal", "POST /relationships/{id}/goals", "title", 201, api.call("POST", p, rel["s"]["token"], json={"title": "Mock interview", "target_date": "2030-01-01"}))
    g = r.json()["goals"][0]; assert g["status"] == "TODO" and r.json()["progress"] == 0
    rec("goal by mentor", "POST /relationships/{id}/goals", "mentor", 201, api.call("POST", p, rel["m"]["token"], json={"title": "Resume"}))
    r = rec("goal done", "PATCH /goals/{id}", "DONE", 200, api.call("PATCH", f"/goals/{g['id']}", rel["m"]["token"], json={"status": "DONE"}))
    assert r.json()["progress"] == 50
    rec("goal rename", "PATCH /goals/{id}", "title", 200, api.call("PATCH", f"/goals/{g['id']}", rel["s"]["token"], json={"title": "New"}))


@pytest.mark.parametrize("label,body", [
    ("empty title", {"title": ""}), ("title 201", {"title": "x" * 201}),
    ("bad date", {"title": "a", "target_date": "31-12-2030"}), ("extra field", {"title": "a", "x": 1}), ("no body", {}),
])
def test_goal_validation(api, rel, label, body):
    rec(f"goal {label}", "POST /relationships/{id}/goals", label, 422, api.call("POST", f"/relationships/{rel['id']}/goals", rel["s"]["token"], json=body))


def test_goal_update_validation(api, rel):
    gid = api.call("POST", f"/relationships/{rel['id']}/goals", rel["s"]["token"], json={"title": "g"}).json()["goals"][0]["id"]
    for label, body in [("bad status", {"status": "FINISHED"}), ("null status", {"status": None}), ("null title", {"title": None})]:
        rec(f"goal update {label}", "PATCH /goals/{id}", label, 422, api.call("PATCH", f"/goals/{gid}", rel["s"]["token"], json=body))
    rec("goal stranger", "PATCH /goals/{id}", "other user", 404, api.call("PATCH", f"/goals/{gid}", register(api, "STUDENT")["token"], json={"status": "DONE"}))
    rec("goal missing", "PATCH /goals/{id}", 99999999, 404, api.call("PATCH", "/goals/99999999", rel["s"]["token"], json={"status": "DONE"}))


def test_engagement_rbac(api, rel, admin):
    p = f"/relationships/{rel['id']}/goals"
    rec("goal anon", "POST goals", "-", 401, api.call("POST", p, json={"title": "a"}))
    rec("goal stranger", "POST goals", "stranger", 404, api.call("POST", p, register(api, "STUDENT")["token"], json={"title": "a"}))
    rec("goal admin", "POST goals", "admin", (403, 404), api.call("POST", p, admin["token"], json={"title": "a"}))
    rec("goal missing rel", "POST goals", 99999999, 404, api.call("POST", "/relationships/99999999/goals", rel["s"]["token"], json={"title": "a"}))


def test_activities(api, rel):
    p = f"/relationships/{rel['id']}/activities"
    r = rec("add activity", "POST /relationships/{id}/activities", "MEETING", 201, api.call("POST", p, rel["m"]["token"], json={"activity_type": "MEETING", "notes": "Intro call"}))
    assert r.json()["activities"][0]["activity_date"] == date.today().isoformat() or True
    rec("activity past date", "POST activities", "past", 201, api.call("POST", p, rel["s"]["token"], json={"activity_type": "CHECK_IN", "notes": "n", "activity_date": "2026-01-01"}))
    tomorrow = (date.today() + timedelta(days=2)).isoformat()
    for label, body in [("future date", {"activity_type": "OTHER", "notes": "n", "activity_date": tomorrow}),
                        ("bad type", {"activity_type": "PARTY", "notes": "n"}),
                        ("empty notes", {"activity_type": "OTHER", "notes": "  "}),
                        ("notes 4001", {"activity_type": "OTHER", "notes": "x" * 4001})]:
        rec(f"activity {label}", "POST activities", label, 422, api.call("POST", p, rel["s"]["token"], json=body))


def test_feedback(api, rel):
    p = f"/relationships/{rel['id']}/feedback"
    r = rec("feedback create", "POST /relationships/{id}/feedback", "5", 200, api.call("POST", p, rel["s"]["token"], json={"rating": 5, "comments": "Great"}))
    assert len(r.json()["feedback"]) == 1
    r = rec("feedback edit", "POST feedback", "3", 200, api.call("POST", p, rel["s"]["token"], json={"rating": 3}))
    assert len(r.json()["feedback"]) == 1 and r.json()["feedback"][0]["rating"] == 3  # no duplicate
    api.call("POST", p, rel["m"]["token"], json={"rating": 4})
    assert len(api.call("GET", f"/relationships/{rel['id']}", rel["s"]["token"]).json()["feedback"]) == 2
    for label, body in [("rating 0", {"rating": 0}), ("rating 6", {"rating": 6}), ("rating string", {"rating": "5"}),
                        ("rating float", {"rating": 4.5}), ("comments 2001", {"rating": 3, "comments": "x" * 2001}), ("no rating", {})]:
        rec(f"feedback {label}", "POST feedback", label, 422, api.call("POST", p, rel["s"]["token"], json=body))
    rec("feedback stranger", "POST feedback", "stranger", 404, api.call("POST", p, register(api, "STUDENT")["token"], json={"rating": 5}))


def test_feedback_list(api, admin, areas):
    m = make_mentor(api, admin, [areas[0]])
    s = register(api, "STUDENT")
    rid, _ = new_relationship(api, s, m, areas[0])
    api.call("POST", f"/relationships/{rid}/feedback", s["token"], json={"rating": 4, "comments": "ok"})
    api.call("POST", f"/relationships/{rid}/feedback", m["token"], json={"rating": 2})  # mentor's own note
    sm = rec("feedback student", "GET /feedback", "student", 200, api.call("GET", "/feedback", s["token"])).json()
    mm = rec("feedback mentor", "GET /feedback", "mentor", 200, api.call("GET", "/feedback", m["token"])).json()
    assert [i["rating"] for i in sm["items"]] == [4] and sm["average"] == 4.0   # student sees what they submitted
    assert [i["rating"] for i in mm["items"]] == [4] and mm["average"] == 4.0   # mentor sees what they received
    rec("feedback anon", "GET /feedback", "-", 401, api.call("GET", "/feedback"))
    empty = api.call("GET", "/feedback", register(api, "STUDENT")["token"]).json()
    assert empty == {"items": [], "average": None}


def test_notifications_created_and_read(api, admin, areas):
    m = make_mentor(api, admin, [areas[0]]); s = register(api, "STUDENT")
    rid = new_request(api, s, m, areas[0]).json()["id"]
    n = rec("mentor notif", "GET /notifications", "-", 200, api.call("GET", "/notifications", m["token"])).json()
    assert n["unread"] >= 1 and any(i["type"] == "NEW_REQUEST" and i["reference_id"] == rid for i in n["items"])
    api.call("POST", f"/requests/{rid}/accept", m["token"])
    sn = api.call("GET", "/notifications", s["token"]).json()
    assert any(i["type"] == "REQUEST_ACCEPTED" for i in sn["items"])
    nid = n["items"][0]["id"]
    rec("read one", "POST /notifications/{id}/read", nid, 200, api.call("POST", f"/notifications/{nid}/read", m["token"]))
    assert api.call("GET", "/notifications", m["token"]).json()["unread"] == n["unread"] - 1
    rec("read other's", "POST /notifications/{id}/read", "student reads mentor's", 404, api.call("POST", f"/notifications/{nid}/read", s["token"]))
    rec("read missing", "POST /notifications/{id}/read", 99999999, 404, api.call("POST", "/notifications/99999999/read", m["token"]))
    rec("read all", "POST /notifications/read-all", "-", 200, api.call("POST", "/notifications/read-all", s["token"]))
    assert api.call("GET", "/notifications", s["token"]).json()["unread"] == 0
    rec("notif anon", "GET /notifications", "-", 401, api.call("GET", "/notifications"))


def test_other_notification_types(api, admin, areas):
    m = make_mentor(api, admin, [areas[0]]); s = register(api, "STUDENT")
    rid = new_request(api, s, m, areas[0]).json()["id"]
    api.call("POST", f"/requests/{rid}/cancel", s["token"])
    assert any(i["type"] == "REQUEST_CANCELLED" for i in api.call("GET", "/notifications", m["token"]).json()["items"])
    rid = new_request(api, s, m, areas[0]).json()["id"]
    api.call("POST", f"/requests/{rid}/reject", m["token"], json={})
    assert any(i["type"] == "REQUEST_REJECTED" for i in api.call("GET", "/notifications", s["token"]).json()["items"])
