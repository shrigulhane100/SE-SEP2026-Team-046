"""HTTP client and small assertion helpers shared by all E2E tests."""
import requests

MSG = "I would like advice on preparing for technical interviews."
MENTOR_TYPES = ["Recent Graduate", "Industry Professional", "Research Mentor", "Entrepreneur", "Faculty"]
CAREER_OBJECTIVES = ["PLACEMENT", "HIGHER_STUDIES", "ENTREPRENEURSHIP", "CAREER_CLARITY"]


class Client:
    """Thin wrapper over requests that prefixes /api/v1 and sends the bearer token."""

    def __init__(self, base, token=None):
        self.base, self.token, self.s = base.rstrip("/"), token, requests.Session()

    def req(self, method, path, **kw):
        headers = kw.pop("headers", {})
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")
        return self.s.request(method, f"{self.base}/api/v1{path}", headers=headers, timeout=20, **kw)

    def get(self, path, **kw): return self.req("GET", path, **kw)
    def post(self, path, json=None, **kw): return self.req("POST", path, json=json, **kw)
    def put(self, path, json=None, **kw): return self.req("PUT", path, json=json, **kw)
    def patch(self, path, json=None, **kw): return self.req("PATCH", path, json=json, **kw)


class Actor:
    """A registered account (student, mentor or admin) with its own authenticated client."""

    def __init__(self, base, user, token, password):
        self.user, self.id, self.email, self.name, self.role = user, user["id"], user["email"], user["name"], user["role"]
        self.password, self.token, self.base = password, token, base
        self.api = Client(base, token)

    def relogin(self):
        r = Client(self.base).post("/auth/login", {"email": self.email, "password": self.password})
        assert r.status_code == 200, r.text
        self.token = r.json()["access_token"]
        self.api = Client(self.base, self.token)
        return self


def ok(r, code=200):
    """Assert the status code and return parsed JSON (None for 204)."""
    assert r.status_code == code, f"{r.request.method} {r.request.path_url} -> {r.status_code} (expected {code}): {r.text[:400]}"
    return None if r.status_code == 204 else r.json()


def fail(r, code, contains=None):
    """Assert an error response and optionally that detail contains a phrase."""
    assert r.status_code == code, f"{r.request.method} {r.request.path_url} -> {r.status_code} (expected {code}): {r.text[:400]}"
    if contains:
        assert contains.lower() in str(r.json().get("detail", "")).lower(), f"detail {r.json()!r} lacks {contains!r}"
    return r.json()
