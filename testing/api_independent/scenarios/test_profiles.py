"""Student and mentor profile management and guidance-area selection."""
import pytest
from .conftest import RUN, mentor_profile, register, student_profile, unique
from .helpers import CAREER_OBJECTIVES, fail, ok


def test_student_profile_create_read_update(new_student, areas, admin):
    s = new_student(complete=False)
    stub = ok(s.api.get("/profile/me"))                                    # registration creates a stub profile
    assert stub["user"]["profile_completion"] < 100 and stub["area_ids"] == []
    body = ok(s.api.put("/profile/me", student_profile([areas[0]["id"], areas[1]["id"]])))
    assert body["user"]["profile_completion"] == 100
    assert set(body["area_ids"]) == {areas[0]["id"], areas[1]["id"]} and body["profile"]["skills"] == ["Python", "SQL"]
    # partial update keeps everything else
    body = ok(s.api.put("/profile/me", {"goals_summary": "New goal"}))
    assert body["profile"]["goals_summary"] == "New goal" and body["profile"]["education"] == "BS Data Science"
    assert set(body["area_ids"]) == {areas[0]["id"], areas[1]["id"]}
    # area_ids replaces; empty list clears
    assert ok(s.api.put("/profile/me", {"area_ids": [areas[2]["id"]]}))["area_ids"] == [areas[2]["id"]]
    assert ok(s.api.put("/profile/me", {"area_ids": []}))["area_ids"] == []
    assert ok(s.api.put("/profile/me", {"name": "Renamed Student"}))["user"]["name"] == "Renamed Student"
    assert ok(s.api.get("/auth/me"))["name"] == "Renamed Student"


@pytest.mark.parametrize("objective", CAREER_OBJECTIVES)
def test_student_career_objective_saved(new_student, objective):
    s = new_student(objective=objective)
    assert ok(s.api.get("/profile/me"))["profile"]["career_objective"] == objective


@pytest.mark.parametrize("bad", [
    {"academic_level": "PhD"}, {"preferred_mode": "Carrier pigeon"}, {"career_objective": "NOPE"}, {"area_ids": [1, 1]}, {"area_ids": [0]},
    {"area_ids": ["a"]}, {"skills": ["x"] * 31}, {"roll_number": None}, {"name": None}, {"name": "A"}, {"unknown": 1}, {"max_mentees": 3}, {"is_accepting": False},
], ids=lambda d: str(d)[:30])
def test_student_profile_rejects_invalid_or_mentor_fields(new_student, bad):
    fail(new_student().api.put("/profile/me", bad), 422)


def test_roll_number_uniqueness_on_update(new_student):
    a, b = new_student(), new_student()
    roll_a = ok(a.api.get("/profile/me"))["profile"]["roll_number"]
    fail(b.api.put("/profile/me", {"roll_number": roll_a.lower()}), 409, "roll number")
    new = f"NEW{RUN}9".upper()
    assert ok(b.api.put("/profile/me", {"roll_number": new}))["profile"]["roll_number"] == new


def test_nonexistent_or_inactive_area_rejected(new_student, admin):
    s = new_student()
    fail(s.api.put("/profile/me", {"area_ids": [999999]}), 422, "do not exist")
    area = ok(admin.api.post("/admin/guidance-areas", {"name": f"Soon inactive {RUN}"}), 201)
    ok(s.api.put("/profile/me", {"area_ids": [area["id"]]}))
    ok(admin.api.patch(f"/admin/guidance-areas/{area['id']}", {"is_active": False}))
    ok(s.api.put("/profile/me", {"area_ids": [area["id"]], "goals_summary": "keeps existing inactive mapping"}))   # documented: kept until removed
    fail(new_student().api.put("/profile/me", {"area_ids": [area["id"]]}), 422, "inactive")                     # but cannot be newly selected


@pytest.mark.parametrize("mtype", ["Recent Graduate", "Industry Professional", "Research Mentor", "Entrepreneur", "Faculty"])
def test_mentor_profile_for_each_mentor_type(new_mentor, mtype):
    m = new_mentor(mentor_type=mtype)
    body = ok(m.api.get("/profile/me"))
    assert body["profile"]["mentor_type"] == mtype and body["user"]["profile_completion"] == 100
    assert body["profile"]["max_mentees"] == 3 and body["profile"]["is_accepting"] is True


def test_mentor_profile_update_rules(new_mentor, areas):
    m = new_mentor(max_mentees=2)
    body = ok(m.api.put("/profile/me", {"bio": "Updated bio", "is_accepting": False}))
    assert body["profile"]["bio"] == "Updated bio" and body["profile"]["is_accepting"] is False
    assert body["profile"]["max_mentees"] == 2 and body["profile"]["current_role"] == "Engineer"   # untouched fields kept
    for bad in ({"max_mentees": 0}, {"max_mentees": 21}, {"max_mentees": "3"}, {"experience_years": -1}, {"experience_years": 61}, {"is_accepting": "yes"}, {"roll_number": "ABCD1234"}, {"academic_level": "Degree"}):
        fail(m.api.put("/profile/me", bad), 422)


def test_admin_has_no_profile(admin):
    assert admin.api.get("/profile/me").status_code == 403
