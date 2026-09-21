from functools import wraps

from flask import Blueprint, abort, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)
DUMMY_HASH = generate_password_hash("not-a-user-password")


@bp.before_app_request
def load_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = (
            get_db()
            .execute("SELECT id, username, role FROM users WHERE id = ? AND active = 1", (user_id,))
            .fetchone()
        )


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        if g.user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        valid = len(password) <= 128 and check_password_hash(
            user["password_hash"] if user else DUMMY_HASH, password
        )
        if user and user["active"] and valid:
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            return redirect(url_for("catalog.dashboard"))
        error = "Usuário ou senha inválidos."
    return render_template("login.html", error=error), 400 if error else 200


@bp.post("/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
