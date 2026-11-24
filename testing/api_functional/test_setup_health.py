"""M3.1: FastAPI and PostgreSQL setup - service health check"""
import pytest
from conftest import PW, rec, register, uid

def test_health(api):
    r = rec("health ok", "GET /health", "-", 200, api.call("GET", "/health"))
    assert r.json() == {"status": "ok", "database": "reachable"}
