"""Race conditions and complete multi-role journeys (run with -s to see each step)."""
from concurrent.futures import ThreadPoolExecutor

from .conftest import RUN
from .helpers import MSG, fail, ok


def test_simultaneous_accepts_never_overbook_a_mentor(new_student, new_mentor, send_request):
    m = new_mentor(max_mentees=1)
    reqs = [send_request(new_student(), m) for _ in range(4)]
    with ThreadPoolExecutor(4) as pool:
        codes = list(pool.map(lambda r: m.api.post(f"/requests/{r['id']}/accept").status_code, reqs))
    assert sorted(codes) == [200, 409, 409, 409], codes
    assert len(ok(m.api.get("/relationships"))) == 1


def test_simultaneous_duplicate_requests_create_only_one(new_student, new_mentor, areas):
    s, m = new_student(), new_mentor(max_mentees=5)
    body = {"mentor_id": m.id, "area_id": areas[0]["id"], "message": MSG, "type": "LONG_TERM"}
    with ThreadPoolExecutor(4) as pool:
        codes = list(pool.map(lambda _: s.api.post("/requests", body).status_code, range(4)))
    assert codes.count(201) == 1 and codes.count(409) == 3, codes


def test_double_accept_race_creates_a_single_relationship(new_student, new_mentor, send_request):
    m = new_mentor(max_mentees=5)
    req = send_request(new_student(), m)
    with ThreadPoolExecutor(3) as pool:
        codes = list(pool.map(lambda _: m.api.post(f"/requests/{req['id']}/accept").status_code, range(3)))
    assert codes.count(200) == 1 and codes.count(409) == 2, codes
    assert len(ok(m.api.get("/relationships"))) == 1


def test_FULL_JOURNEY_all_roles(anon, admin, areas, new_student, new_mentor):
    """Register -> profile -> admin verifies -> discover -> request -> accept -> mentor -> feedback -> admin view."""
    step = lambda n, t: print(f"\n  [{n:02}] {t}")
    from .conftest import register, unique, student_profile, mentor_profile
    a = areas[0]["id"]
    step(1, "Student registers and completes profile")
    stu = register({"role": "STUDENT", "name": "Journey Student", "email": f"{unique('js')}@example.com", "roll_number": f"J{RUN}1", "career_objective": "PLACEMENT"})
    assert ok(stu.api.put("/profile/me", student_profile([a])))["user"]["profile_completion"] == 100
    step(2, "Mentor registers (PENDING) and completes profile")
    men = register({"role": "MENTOR", "name": "Journey Mentor", "email": f"{unique('jm')}@example.com", "mentor_type": "Faculty"})
    ok(men.api.put("/profile/me", mentor_profile([a], mentor_type="Faculty", max_mentees=1)))
    step(3, "Student cannot yet see or request the unverified mentor")
    fail(stu.api.get(f"/mentors/{men.id}"), 404)
    step(4, "Admin sees the mentor in the queue and verifies")
    assert any(x["id"] == men.id and x["verification_status"] == "PENDING" for x in ok(admin.api.get("/admin/mentor-verifications")))
    ok(admin.api.post(f"/admin/mentors/{men.id}/verify", {"approve": True}))
    step(5, "Student discovers mentor with a 100% match")
    hit = next(x for x in ok(stu.api.get("/mentors", params={"q": "Journey Mentor"})) if x["id"] == men.id)
    assert hit["match"] == 100 and hit["available"] is True
    step(6, "Student sends request; mentor is notified")
    req = ok(stu.api.post("/requests", {"mentor_id": men.id, "area_id": a, "message": MSG, "objective": "Placement", "type": "LONG_TERM"}), 201)
    assert ok(men.api.get("/notifications"))["unread"] >= 1
    step(7, "Mentor accepts -> relationship ACTIVE, mentor now at capacity")
    rel = ok(men.api.post(f"/requests/{req['id']}/accept"))["relationship"]
    assert ok(stu.api.get(f"/mentors/{men.id}"))["available"] is False
    step(8, "Both set goals and log activities")
    ok(men.api.post(f"/relationships/{rel['id']}/goals", {"title": "Resume"}), 201)
    gid = ok(stu.api.post(f"/relationships/{rel['id']}/goals", {"title": "Mock interviews"}), 201)["goals"][-1]["id"]
    ok(men.api.post(f"/relationships/{rel['id']}/activities", {"activity_type": "RESUME_REVIEW", "notes": "Reviewed"}), 201)
    step(9, "Student pauses then resumes; completes a goal")
    ok(stu.api.patch(f"/relationships/{rel['id']}/status", {"status": "PAUSED"})); ok(men.api.patch(f"/relationships/{rel['id']}/status", {"status": "ACTIVE"}))
    assert ok(stu.api.patch(f"/goals/{gid}", {"status": "DONE"}))["progress"] == 50
    step(10, "Mentoring completes; both leave feedback")
    ok(men.api.patch(f"/relationships/{rel['id']}/status", {"status": "COMPLETED"}))
    ok(stu.api.post(f"/relationships/{rel['id']}/feedback", {"rating": 5, "comments": "Great"})); ok(men.api.post(f"/relationships/{rel['id']}/feedback", {"rating": 4}))
    assert ok(men.api.get("/feedback"))["average"] == 5.0
    step(11, "Slot is freed; admin sees users and area usage but cannot read mentoring data")
    assert ok(stu.api.get(f"/mentors/{men.id}"))["available"] is True
    assert {stu.id, men.id} <= {u["id"] for u in ok(admin.api.get("/admin/users", params={"q": "Journey"}))}
    assert next(x for x in ok(admin.api.get("/admin/guidance-areas")) if x["id"] == a)["requests"] >= 1
    assert admin.api.get(f"/relationships/{rel['id']}").status_code == 403
    step(12, "Logout revokes the session")
    ok(stu.api.post("/auth/logout"), 204); fail(stu.api.get("/auth/me"), 401)
    print("\n  Journey complete.")
