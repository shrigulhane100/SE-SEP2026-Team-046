"""M3.8: Edge cases and malicious-input checks (injection, pagination)"""
import pytest
from conftest import PW, make_mentor, rec, register, uid

def test_sql_injection_login(api):
    r = api.call("POST", "/auth/login", json={"email": "a@b.com", "password": "' OR '1'='1"})
    rec("sqli login", "POST /auth/login", "' OR '1'='1", 401, r)


def test_injection_in_q(api, student1):
    rec("sqli q", "GET /mentors?q", "'; DROP TABLE users;--", 200, api.call("GET", "/mentors", student1["token"], params={"q": "'; DROP TABLE users;--"}))
    assert api.call("GET", "/auth/me", student1["token"]).status_code == 200


def test_pagination(api, student1):
    a = api.call("GET", "/mentors", student1["token"], params={"limit": 1, "offset": 0}).json()
    b = api.call("GET", "/mentors", student1["token"], params={"limit": 1, "offset": 1}).json()
    assert len(a) == 1 and (not b or a[0]["id"] != b[0]["id"])
