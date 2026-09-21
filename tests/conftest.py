import re

import pytest
from werkzeug.security import generate_password_hash

from ael import create_app
from ael.db import get_db, migrate


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.sqlite3"),
            "SECRET_KEY": "only-for-automated-tests-not-production",
        }
    )
    with app.app_context():
        connection = get_db()
        migrate(connection)
        with connection:
            connection.execute(
                "INSERT INTO users(username, password_hash, role) VALUES (?, ?, 'admin')",
                ("admin", generate_password_hash("test-password-123")),
            )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def login(client):
    return client.post(
        "/login",
        data={
            "username": "admin",
            "password": "test-password-123",
            "csrf_token": csrf(client),
        },
    )


@pytest.fixture
def admin(client):
    login(client)
    return client


def material(**kwargs):
    data = {"code": "EPI-001", "name": "Luva de proteção", "category": "EPI", "unit": "PAR"}
    return data | kwargs


def location(**kwargs):
    return {"code": "BASE-01", "name": "Estante A", "address": "Corredor A / Estante 01"} | kwargs


def submit(client, kind="materials", data=None, path=None):
    path = path or f"/catalog/{kind}/new"
    values = data if data is not None else material()
    return client.post(path, data=values | {"csrf_token": csrf(client, path)})
