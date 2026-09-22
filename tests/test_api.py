import pytest

from ael.db import get_db
from tests.conftest import material, submit


def token(client):
    return {"X-CSRFToken": client.get("/api/csrf").json["csrf_token"]}


@pytest.mark.parametrize("path", ["/api/materiais", "/api/materiais/1", "/api/csrf"])
def test_reads_require_login(client, path):
    response = client.get(path)
    assert response.status_code == 401
    assert response.json["error"]["code"] == "unauthorized"
    assert "Location" not in response.headers


def test_create_detail_and_audit(admin, app):
    response = admin.post("/api/materiais", json=material(), headers=token(admin))
    assert response.status_code == 201
    row = response.json["data"]
    assert row["active"] is True
    assert response.headers["Location"] == f"/api/materiais/{row['id']}"
    assert admin.get(response.headers["Location"]).json["data"] == row
    with app.app_context():
        event = get_db().execute("SELECT * FROM audit_events").fetchone()
        assert event["entity"] == "materials"
        assert event["entity_id"] == row["id"]
        assert event["actor_id"] == 1
        assert event["action"] == "create"


def test_duplicate_code(admin, app):
    headers = token(admin)
    admin.post("/api/materiais", json=material(), headers=headers)
    response = admin.post("/api/materiais", json=material(code="epi-001"), headers=headers)
    assert response.status_code == 409
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM materials").fetchone()[0] == 1
        assert get_db().execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"code": "AA"},
        material(name=None),
        material(name=3),
        material(active=True),
        material(category="INVALID"),
        material(code="!"),
    ],
)
def test_reject_invalid_json_values(admin, app, payload):
    response = admin.post("/api/materiais", json=payload, headers=token(admin))
    assert response.status_code in (400, 415)
    assert response.is_json
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM materials").fetchone()[0] == 0


def test_missing_and_invalid_csrf(admin):
    assert admin.post("/api/materiais", json=material()).json["error"]["code"] == "csrf_error"
    response = admin.post("/api/materiais", json=material(), headers={"X-CSRFToken": "invalid"})
    assert response.status_code == 400


def test_role_and_deactivated_user(admin, app):
    headers = token(admin)
    with app.app_context():
        db = get_db()
        with db:
            db.execute("UPDATE users SET role='almoxarife' WHERE id=1")
    assert admin.get("/api/materiais").status_code == 403
    assert admin.post("/api/materiais", json=material(), headers=headers).status_code == 403
    with app.app_context():
        db = get_db()
        with db:
            db.execute("UPDATE users SET active=0 WHERE id=1")
    assert admin.get("/api/materiais").status_code == 401


def test_pagination_search_and_status(admin, app):
    submit(admin, data=material(code="AA-01", name="Parafuso"))
    submit(admin, data=material(code="BB-01", name="Luva"))
    result = admin.get("/api/materiais?per_page=1&page=2").json
    assert result["pagination"] == {"page": 2, "per_page": 1, "total": 2}
    assert result["data"][0]["code"] == "AA-01"
    assert admin.get("/api/materiais?q=luva").json["pagination"]["total"] == 1
    assert admin.get("/api/materiais?q=%25").json["data"] == []
    assert admin.get("/api/materiais?q=' OR 1=1--").json["data"] == []
    with app.app_context():
        db = get_db()
        with db:
            db.execute("UPDATE materials SET active=0 WHERE code='AA-01'")
    assert admin.get("/api/materiais").json["pagination"]["total"] == 1
    assert admin.get("/api/materiais?status=all").json["pagination"]["total"] == 2
    assert admin.get("/api/materiais?status=inactive").json["data"][0]["active"] is False


@pytest.mark.parametrize(
    "query", ["page=0", "page=bad", "per_page=101", "per_page=-1", "status=other", "q=" + "a" * 101]
)
def test_invalid_filters(admin, query):
    assert admin.get("/api/materiais?" + query).status_code == 400


def test_http_errors_are_json(admin):
    assert admin.get("/api/materiais/999").status_code == 404
    assert admin.get("/api/unknown").is_json
    headers = token(admin)
    response = admin.post(
        "/api/materiais", data="{", content_type="application/json", headers=headers
    )
    assert response.status_code == 400 and response.is_json
    response = admin.post("/api/materiais", data="x", content_type="text/plain", headers=headers)
    assert response.status_code == 415 and response.is_json
    response = admin.put("/api/materiais", json={}, headers=headers)
    assert response.status_code == 405 and response.is_json
    assert "GET" in response.headers["Allow"]
    response = admin.post(
        "/api/materiais", data="x" * 70000, content_type="application/json", headers=headers
    )
    assert response.status_code == 413 and response.is_json


def test_api_uses_atomic_audit(admin, app, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("audit failed")

    monkeypatch.setattr("ael.services.audit", fail)
    headers = token(admin)
    with pytest.raises(RuntimeError, match="audit failed"):
        admin.post("/api/materiais", json=material(), headers=headers)
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM materials").fetchone()[0] == 0
