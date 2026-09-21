import os
import secrets
from pathlib import Path

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from . import auth, catalog, db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=str(Path(app.instance_path) / "ael.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("AEL_HTTPS") == "1",
        PERMANENT_SESSION_LIFETIME=3600,
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config.get("SECRET_KEY"):
        key_path = Path(app.instance_path) / "secret.key"
        key = os.environ.get("AEL_SECRET_KEY")
        if not key:
            try:
                with key_path.open("x", encoding="utf-8") as file:
                    file.write(secrets.token_hex(32))
                key_path.chmod(0o600)
            except FileExistsError:
                pass
            key = key_path.read_text(encoding="utf-8").strip()
        if len(key) < 32:
            raise ValueError("AEL_SECRET_KEY deve ter pelo menos 32 caracteres.")
        app.config["SECRET_KEY"] = key
    CSRFProtect(app)
    db.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(catalog.bp)

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template(
            "error.html",
            message="Formulário expirado ou inválido. Volte, atualize a página e tente novamente.",
        ), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", message="Seu perfil não tem acesso a esta etapa."), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", message="Página ou cadastro não encontrado."), 404

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    return app
