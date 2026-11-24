"""Student mentor discovery: search, filters, ranking, pagination, and public listing."""
import pytest
from .conftest import RUN
from .helpers import MENTOR_TYPES, fail, ok


def ids(rows): return [r["id"] for r in rows]


def test_public_list_hides_unverified_and_rejected(anon, new_mentor):
    v, p = new_mentor(), new_mentor(verify=False)
    got = ids(ok(anon.get("/public/mentors", params={"limit": 100})))
    assert v.id in got or ok(anon.get("/public/mentors", params={"q": v.name}))   # may be beyond the first page
    assert p.id not in ids(ok(anon.get("/public/mentors", params={"q": p.name})))
    row = ok(anon.get("/public/mentors", params={"q": v.name}))[0]
    assert row["match"] is None and "email" not in row and row["verification_status"] == "VERIFIED"


def test_student_search_and_every_filter(new_student, new_mentor, areas):
    a, b = areas[0]["id"], areas[1]["id"]
    ind = f"Industry-{RUN}-disc"
    m1 = new_mentor(area_ids=[a], industry=ind, experience_years=2, skills=["Rust"], mentor_type="Faculty")
    m2 = new_mentor(area_ids=[b], industry=ind, experience_years=9, skills=["Go"], mentor_type="Entrepreneur")
    m3 = new_mentor(area_ids=[a, b], industry=ind, experience_years=15, skills=["Rust"], mentor_type="Faculty", is_accepting=False)
    s = new_student(area_ids=[a])
    q = lambda **p: ids(ok(s.api.get("/mentors", params={"industry": ind, "limit": 100, **p})))
    assert set(q()) == {m1.id, m2.id, m3.id}
    assert set(q(area_id=a)) == {m1.id, m3.id} and set(q(area_id=b)) == {m2.id, m3.id}
    assert set(q(mentor_type="Faculty")) == {m1.id, m3.id}
    assert set(q(min_experience=9)) == {m2.id, m3.id}
    assert set(q(q="rust")) == {m1.id, m3.id} and set(q(q=m2.name.upper())) == {m2.id}
    assert set(q(availability="available")) == {m1.id, m2.id} and q(availability="unavailable") == [m3.id]
    assert q(sort="experience") == [m3.id, m2.id, m1.id]
    assert q(sort="relevance")[0] == m1.id                # available first, then best area overlap
    assert q(q="no-match-" + RUN) == []
    assert len(q(limit=2)) == 2 and q(offset=2, limit=100) == q()[2:]


def test_match_score_reflects_guidance_overlap(new_student, new_mentor, areas):
    a, b = areas[0]["id"], areas[1]["id"]
    m_both, m_one = new_mentor(area_ids=[a, b]), new_mentor(area_ids=[a])
    s = new_student(area_ids=[a, b])
    got = {r["id"]: r["match"] for r in ok(s.api.get("/mentors", params={"q": "Mentor", "limit": 100}))}
    assert got[m_both.id] == 100 and got[m_one.id] == 50
    assert all(r["match"] is None for r in ok(new_student(area_ids=[]).api.get("/mentors", params={"limit": 5})))


def test_mentor_detail_and_availability_flags(new_student, new_mentor):
    m, s = new_mentor(max_mentees=4), new_student()
    d = ok(s.api.get(f"/mentors/{m.id}"))
    assert d["id"] == m.id and d["available"] is True and d["max_mentees"] == 4 and d["active_mentees"] == 0
    assert d["areas"] and d["skills"] == ["Python", "Design"] and d["current_role"] == "Engineer"
    ok(m.api.put("/profile/me", {"is_accepting": False}))
    d = ok(s.api.get(f"/mentors/{m.id}"))
    assert d["available"] is False and d["is_accepting"] is False
    fail(s.api.get("/mentors/999999"), 404)
    fail(s.api.get(f"/mentors/{s.id}"), 404)          # a student id is not a mentor


@pytest.mark.parametrize("mtype", MENTOR_TYPES)
def test_each_mentor_type_is_discoverable(new_student, new_mentor, mtype):
    m = new_mentor(mentor_type=mtype, industry=f"T-{RUN}-{mtype[:4]}")
    rows = ok(new_student().api.get("/mentors", params={"mentor_type": mtype, "q": m.name}))
    assert m.id in ids(rows) and rows[0]["mentor_type"] == mtype


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"min_experience": -1}, {"min_experience": 61}, {"sort": "random"}, {"availability": "maybe"}, {"area_id": 0}, {"area_id": "x"}])
def test_invalid_query_params_rejected(new_student, params):
    fail(new_student().api.get("/mentors", params=params), 422)
