import json
import sqlite3

import pytest

from ael.db import get_db
from ael.services import save_record
from tests.conftest import csrf, location, material, submit


@pytest.mark.parametrize("kind,data", [("materials", material()), ("locations", location())])
def test_create_persists_record_and_actor_audit(app, admin, kind, data):
    response = submit(admin, kind, data)
    assert response.status_code == 302
    with app.app_context():
        connection = get_db()
        record = connection.execute(f"SELECT * FROM {kind}").fetchone()
        event = connection.execute("SELECT * FROM audit_events").fetchone()
        assert record["name"] == data["name"]
        assert event["actor_id"] == 1
        assert event["action"] == "create"
        assert json.loads(event["after_json"])["code"] == data["code"]
        assert event["before_json"] is None


@pytest.mark.parametrize(
    "data",
    [
        material(name=" "),
        material(name="x" * 101),
        material(code="' OR 1=1 --"),
        material(code="A"),
        material(category="Inválida"),
        material(unit="Litro"),
    ],
)
def test_invalid_material_does_not_write(app, admin, data):
    assert submit(admin, data=data).status_code == 400
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM materials").fetchone()[0] == 0
        assert get_db().execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0


@pytest.mark.parametrize("address", ["", " ", "x" * 161])
def test_invalid_address(app, admin, address):
    assert submit(admin, "locations", location(address=address)).status_code == 400


@pytest.mark.parametrize("kind,data", [("materials", material()), ("locations", location())])
def test_unique_code_is_normalized(app, admin, kind, data):
    assert submit(admin, kind, data).status_code == 302
    assert submit(admin, kind, data | {"code": data["code"].lower()}).status_code == 400
    with app.app_context():
        assert get_db().execute(f"SELECT count(*) FROM {kind}").fetchone()[0] == 1
        assert get_db().execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


@pytest.mark.parametrize("kind,data", [("materials", material()), ("locations", location())])
def test_edit_status_and_stale_update_preserve_history(app, admin, kind, data):
    submit(admin, kind, data)
    path = f"/catalog/{kind}/1/edit"
    assert (
        submit(admin, kind, data | {"name": "Nome novo", "version": "1"}, path).status_code == 302
    )
    assert (
        submit(admin, kind, data | {"name": "Nome antigo", "version": "1"}, path).status_code == 400
    )
    token = csrf(admin, path)
    assert (
        admin.post(
            f"/catalog/{kind}/1/status",
            data={
                "active": "0",
                "version": "2",
                "csrf_token": token,
            },
        ).status_code
        == 302
    )
    with app.app_context():
        record = get_db().execute(f"SELECT * FROM {kind}").fetchone()
        assert record["name"] == "Nome novo"
        assert record["active"] == 0
        events = get_db().execute("SELECT * FROM audit_events ORDER BY id").fetchall()
        assert [e["action"] for e in events] == ["create", "update", "deactivate"]
        assert json.loads(events[1]["before_json"])["name"] == data["name"]
    assert (
        admin.post(
            f"/catalog/{kind}/1/status",
            data={
                "active": "1",
                "version": "3",
                "csrf_token": token,
            },
        ).status_code
        == 302
    )
    with app.app_context():
        assert get_db().execute(f"SELECT active FROM {kind}").fetchone()[0] == 1
        assert (
            get_db().execute("SELECT action FROM audit_events ORDER BY id DESC").fetchone()[0]
            == "reactivate"
        )


def test_code_cannot_be_reassigned(admin):
    submit(admin)
    assert (
        submit(
            admin, data=material(code="NEW-01", version="1"), path="/catalog/materials/1/edit"
        ).status_code
        == 400
    )


def test_search_filters_and_escape(admin):
    submit(admin)
    html = admin.get("/catalog/materials?q=EPI-001").get_data(as_text=True)
    assert "Luva de proteção" in html
    assert "Luva de proteção" not in admin.get("/catalog/materials?q=%25").get_data(as_text=True)
    assert "Luva de proteção" not in admin.get("/catalog/materials?status=inactive").get_data(
        as_text=True
    )
    assert admin.get("/catalog/materials?q=%27+OR+1=1+--").status_code == 200


def test_html_is_escaped(admin):
    submit(admin, data=material(name="<script>alert(1)</script>"))
    html = admin.get("/catalog/materials").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_audit_failure_rolls_back_catalog_write(app):
    with app.app_context():
        # An invalid actor causes the audit foreign key to fail after the material insert.
        with pytest.raises(ValueError):
            save_record("materials", material(), actor_id=999)
        assert get_db().execute("SELECT count(*) FROM materials").fetchone()[0] == 0


def test_database_constraints_even_without_form(app):
    with app.app_context():
        with pytest.raises(sqlite3.IntegrityError):
            with get_db() as connection:
                connection.execute(
                    "INSERT INTO materials(code,name,category,unit) VALUES (?,?,?,?)",
                    ("AB", "Luva", "EPI", "INVALID"),
                )


@pytest.mark.parametrize("path", ["/catalog/nope", "/catalog/materials/999/edit"])
def test_not_found(admin, path):
    assert admin.get(path).status_code == 404


def test_invalid_status_does_not_change_record(app, admin):
    submit(admin)
    token = csrf(admin, "/catalog/materials")
    assert (
        admin.post(
            "/catalog/materials/1/status",
            data={
                "active": "2",
                "version": "1",
                "csrf_token": token,
            },
        ).status_code
        == 400
    )
    with app.app_context():
        assert get_db().execute("SELECT active FROM materials").fetchone()[0] == 1
