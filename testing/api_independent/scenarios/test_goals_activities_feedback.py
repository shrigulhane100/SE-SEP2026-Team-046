"""Goals, activities and feedback for both participants, including closed-relationship rules."""
from datetime import UTC, datetime, timedelta

import pytest
from .helpers import fail, ok

ACTIVITY_TYPES = ["MEETING", "RESUME_REVIEW", "MOCK_INTERVIEW", "CHECK_IN", "OTHER"]
today = lambda: datetime.now(UTC).date()


def test_goals_created_by_both_roles_with_progress(active_pair):
    s, m, req, rel = active_pair()
    base = f"/relationships/{rel['id']}/goals"
    r = ok(m.api.post(base, {"title": "  Mock interview x3  ", "target_date": str(today() + timedelta(days=30))}), 201)
    g1 = r["goals"][0]
    assert g1["title"] == "Mock interview x3" and g1["status"] == "TODO" and g1["created_by"] == m.id and g1["created_by_name"] == m.name and r["progress"] == 0
    r = ok(s.api.post(base, {"title": "Update resume"}), 201)
    g2 = next(g for g in r["goals"] if g["title"] == "Update resume")
    assert g2["created_by"] == s.id and g2["target_date"] is None
    r = ok(s.api.patch(f"/goals/{g1['id']}", {"status": "IN_PROGRESS"}))
    assert r["progress"] == 0
    r = ok(m.api.patch(f"/goals/{g1['id']}", {"status": "DONE"}))
    assert r["progress"] == 50
    r = ok(m.api.patch(f"/goals/{g2['id']}", {"status": "DONE", "title": "Resume updated"}))
    assert r["progress"] == 100 and {g["title"] for g in r["goals"]} == {"Mock interview x3", "Resume updated"}
    r = ok(s.api.patch(f"/goals/{g2['id']}", {"status": "TODO"}))
    assert r["progress"] == 50                                         # moving back lowers progress
    assert ok(s.api.get(f"/relationships/{rel['id']}"))["progress"] == 50


@pytest.mark.parametrize("body", [{}, {"title": ""}, {"title": "   "}, {"title": "x" * 201}, {"title": "ok", "target_date": "tomorrow"}, {"title": "ok", "x": 1}])
def test_goal_create_validation(active_pair, body):
    s, m, req, rel = active_pair()
    fail(s.api.post(f"/relationships/{rel['id']}/goals", body), 422)


@pytest.mark.parametrize("body", [{"status": "NOPE"}, {"status": None}, {"title": None}, {"title": ""}, {"x": 1}])
def test_goal_update_validation(active_pair, body):
    s, m, req, rel = active_pair()
    gid = ok(s.api.post(f"/relationships/{rel['id']}/goals", {"title": "A goal"}), 201)["goals"][0]["id"]
    fail(s.api.patch(f"/goals/{gid}", body), 422)


def test_goal_access_control(active_pair, new_student, new_mentor):
    s, m, req, rel = active_pair()
    gid = ok(s.api.post(f"/relationships/{rel['id']}/goals", {"title": "Private goal"}), 201)["goals"][0]["id"]
    for stranger in (new_student(), new_mentor()):
        fail(stranger.api.patch(f"/goals/{gid}", {"status": "DONE"}), 404)
        fail(stranger.api.post(f"/relationships/{rel['id']}/goals", {"title": "Hack"}), 404)
    fail(s.api.patch("/goals/999999", {"status": "DONE"}), 404)


@pytest.mark.parametrize("atype", ACTIVITY_TYPES)
def test_every_activity_type_logged_by_both_roles(active_pair, atype):
    s, m, req, rel = active_pair()
    r = ok(m.api.post(f"/relationships/{rel['id']}/activities", {"activity_type": atype, "notes": "  Mentor note  "}), 201)
    a = r["activities"][0]
    assert a["activity_type"] == atype and a["notes"] == "Mentor note" and a["activity_date"] == str(today()) and a["created_by_name"] == m.name
    r = ok(s.api.post(f"/relationships/{rel['id']}/activities", {"activity_type": atype, "notes": "Student note", "activity_date": str(today() - timedelta(days=2))}), 201)
    assert len(r["activities"]) == 2


@pytest.mark.parametrize("body", [{"notes": "x"}, {"activity_type": "MEETING"}, {"activity_type": "PARTY", "notes": "x"}, {"activity_type": "MEETING", "notes": " "},
                                  {"activity_type": "MEETING", "notes": "x" * 4001}, {"activity_type": "MEETING", "notes": "x", "activity_date": "2999-01-01"}, {"activity_type": "MEETING", "notes": "x", "extra": 1}])
def test_activity_validation(active_pair, body):
    s, m, req, rel = active_pair()
    fail(s.api.post(f"/relationships/{rel['id']}/activities", body), 422)


def test_feedback_from_both_sides_upsert_and_validation(active_pair):
    s, m, req, rel = active_pair()
    path = f"/relationships/{rel['id']}/feedback"
    r = ok(s.api.post(path, {"rating": 4, "comments": " Helpful "}))
    assert r["feedback"][0]["rating"] == 4 and r["feedback"][0]["comments"] == "Helpful" and r["feedback"][0]["given_by"] == s.id
    r = ok(s.api.post(path, {"rating": 5}))                           # edit, not duplicate
    assert len(r["feedback"]) == 1 and r["feedback"][0]["rating"] == 5 and r["feedback"][0]["comments"] == ""
    r = ok(m.api.post(path, {"rating": 3, "comments": "Great student"}))
    assert {f["given_by"] for f in r["feedback"]} == {s.id, m.id}
    for bad in ({"rating": 0}, {"rating": 6}, {"rating": "5"}, {"rating": 4.5}, {}, {"rating": 3, "comments": "c" * 2001}, {"rating": 3, "x": 1}):
        fail(s.api.post(path, bad), 422)


def test_feedback_lists_for_student_and_mentor(new_student, new_mentor, send_request):
    m = new_mentor(max_mentees=5)
    s1, s2 = new_student(), new_student()
    rels = [ok(m.api.post(f"/requests/{send_request(s, m)['id']}/accept"))["relationship"] for s in (s1, s2)]
    assert ok(m.api.get("/feedback")) == {"items": [], "average": None}
    ok(s1.api.post(f"/relationships/{rels[0]['id']}/feedback", {"rating": 5, "comments": "Excellent"}))
    ok(s2.api.post(f"/relationships/{rels[1]['id']}/feedback", {"rating": 4}))
    ok(m.api.post(f"/relationships/{rels[0]['id']}/feedback", {"rating": 1, "comments": "own feedback is excluded"}))
    mine = ok(m.api.get("/feedback"))
    assert mine["average"] == 4.5 and {i["given_by"] for i in mine["items"]} == {s1.id, s2.id} and all(i["area"] for i in mine["items"])
    assert [i["rating"] for i in ok(s1.api.get("/feedback"))["items"]] == [5]          # student sees only feedback they gave
    assert ok(new_mentor().api.get("/feedback"))["items"] == []


def test_completed_and_closed_relationships_are_read_only_except_feedback(active_pair):
    for final in ("COMPLETED", "CLOSED"):
        s, m, req, rel = active_pair()
        gid = ok(s.api.post(f"/relationships/{rel['id']}/goals", {"title": "Before ending"}), 201)["goals"][0]["id"]
        ok(m.api.patch(f"/relationships/{rel['id']}/status", {"status": final}))
        fail(s.api.post(f"/relationships/{rel['id']}/goals", {"title": "Too late"}), 409, "no longer open")
        fail(m.api.patch(f"/goals/{gid}", {"status": "DONE"}), 409, "no longer open")
        fail(m.api.post(f"/relationships/{rel['id']}/activities", {"activity_type": "OTHER", "notes": "late"}), 409, "no longer open")
        assert ok(s.api.post(f"/relationships/{rel['id']}/feedback", {"rating": 5, "comments": "Thanks"}))["feedback"][0]["rating"] == 5   # still allowed


def test_paused_relationship_still_allows_goals_and_activities(active_pair):
    s, m, req, rel = active_pair()
    ok(s.api.patch(f"/relationships/{rel['id']}/status", {"status": "PAUSED"}))
    ok(s.api.post(f"/relationships/{rel['id']}/goals", {"title": "While paused"}), 201)
    ok(m.api.post(f"/relationships/{rel['id']}/activities", {"activity_type": "CHECK_IN", "notes": "Checking in"}), 201)


def test_strangers_and_admin_cannot_touch_engagement_data(active_pair, new_student, new_mentor, admin):
    s, m, req, rel = active_pair()
    for stranger in (new_student(), new_mentor()):
        fail(stranger.api.post(f"/relationships/{rel['id']}/activities", {"activity_type": "OTHER", "notes": "x"}), 404)
        fail(stranger.api.post(f"/relationships/{rel['id']}/feedback", {"rating": 1}), 404)
    assert admin.api.post(f"/relationships/{rel['id']}/goals", {"title": "x"}).status_code == 403
    assert admin.api.get("/feedback").status_code == 403
