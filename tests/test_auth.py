import pytest
from werkzeug.security import check_password_hash

from ael.db import get_db
from tests.conftest import csrf, login, material


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/catalog/materials",
        "/catalog/locations",
        "/catalog/materials/new",
        "/catalog/locations/1/edit",
    ],
)
def test_anonymous_cannot_read(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert response.location.endswith("/login")


@pytest.mark.parametrize(
    "path",
    [
        "/catalog/materials/new",
        "/catalog/locations/new",
        "/catalog/materials/1/edit",
        "/catalog/materials/1/status",
    ],
)
def test_anonymous_cannot_write(app, client, path):
    response = client.post(path, data=material() | {"csrf_token": csrf(client)})
    assert response.status_code == 302
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM materials").fetchone()[0] == 0


@pytest.mark.parametrize("role", ["almoxarife", "solicitante", "aprovador"])
def test_unimplemented_profiles_are_denied_everywhere(app, admin, role):
    token = csrf(admin, "/catalog/materials")
    with app.app_context():
        with get_db() as connection:
            connection.execute("UPDATE users SET role=? WHERE id=1", (role,))
    for path in ["/", "/catalog/materials", "/catalog/locations/new"]:
        assert admin.get(path).status_code == 403
    for path in [
        "/catalog/materials/new",
        "/catalog/materials/1/edit",
        "/catalog/materials/1/status",
        "/catalog/locations/new",
    ]:
        assert admin.post(path, data={"csrf_token": token}).status_code == 403


def test_login_logout_and_cookie(client):
    response = login(client)
    assert response.status_code == 302
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert client.get("/").status_code == 200
    token = csrf(client, "/")
    assert client.post("/logout", data={"csrf_token": token}).status_code == 302
    assert client.get("/").status_code == 302


def test_wrong_login(client):
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "wrong",
            "csrf_token": csrf(client),
        },
    )
    assert response.status_code == 400
    assert client.get("/").status_code == 302


def test_inactive_user_session_is_rejected(app, admin):
    with app.app_context():
        with get_db() as connection:
            connection.execute("UPDATE users SET active=0 WHERE id=1")
    assert admin.get("/").status_code == 302


def test_csrf_required_for_login_and_write(client, admin):
    assert client.post("/login", data={}).status_code == 400
    assert admin.post("/catalog/materials/new", data=material()).status_code == 400
    assert admin.post("/logout").status_code == 400


def test_password_is_hashed_and_headers_present(app, admin):
    with app.app_context():
        value = get_db().execute("SELECT password_hash FROM users").fetchone()[0]
        assert value != "test-password-123"
        assert check_password_hash(value, "test-password-123")
    response = admin.get("/")
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_logout_is_post_only(admin):
    assert admin.get("/logout").status_code == 405
