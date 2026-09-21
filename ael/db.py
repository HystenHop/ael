import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from werkzeug.security import generate_password_hash

MIGRATIONS = Path(__file__).parent / "migrations"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def migrate(connection, directory=MIGRATIONS):
    # Execute each complete SQL statement inside one transaction per version.
    # executescript() is deliberately avoided: it commits pending transactions.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    connection.commit()
    for path in sorted(Path(directory).glob("*.sql")):
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            exists = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (path.name,)
            ).fetchone()
            if exists:
                continue
            statement = ""
            for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
                statement += line
                if sqlite3.complete_statement(statement):
                    connection.execute(statement)
                    statement = ""
            if statement.strip():
                raise ValueError(f"SQL incompleto: {path.name}")
            connection.execute("INSERT INTO schema_migrations(version) VALUES (?)", (path.name,))


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Apply pending migrations without deleting existing data."""
        migrate(get_db())
        click.echo("Banco atualizado. Dados existentes preservados.")

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Nome de usuário")
    @click.password_option(confirmation_prompt=True)
    def create_admin(username, password):
        """Create a local administrator; no default password."""
        username = username.strip().lower()
        if (
            not 3 <= len(username) <= 40
            or not username.isascii()
            or not all(c.isalnum() or c in "._-" for c in username)
        ):
            raise click.ClickException("Use 3 a 40 letras, números, ponto, hífen ou sublinhado.")
        if not 12 <= len(password) <= 128:
            raise click.ClickException("A senha deve ter entre 12 e 128 caracteres.")
        try:
            with get_db() as connection:
                connection.execute(
                    "INSERT INTO users(username, password_hash, role) VALUES (?, ?, 'admin')",
                    (username, generate_password_hash(password)),
                )
        except sqlite3.IntegrityError as error:
            raise click.ClickException("Esse usuário já existe.") from error
        click.echo("Administrador criado.")

    @app.cli.command("seed-demo")
    @click.option("--username", required=True)
    def seed_demo(username):
        """Add fictional examples once, preserving existing records."""
        from .services import seed_examples

        try:
            seed_examples(username.strip().lower())
        except ValueError as error:
            raise click.ClickException(str(error)) from error
        click.echo("Exemplos fictícios preparados. Cadastros existentes não foram alterados.")
