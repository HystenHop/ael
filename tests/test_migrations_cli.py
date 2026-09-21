import shutil
import sqlite3

import pytest

from ael.db import MIGRATIONS, get_db, migrate


def test_upgrade_existing_database_preserves_data(tmp_path):
    old = tmp_path / "old"
    old.mkdir()
    shutil.copy(MIGRATIONS / "001_foundation.sql", old)
    connection = sqlite3.connect(tmp_path / "existing.sqlite3")
    try:
        migrate(connection, old)
        connection.execute(
            "INSERT INTO materials(code, name, category, unit) VALUES ('EPI-01','Luva','EPI','PAR')"
        )
        connection.commit()
        migrate(connection)
        migrate(connection)
        assert connection.execute("SELECT name FROM materials").fetchone()[0] == "Luva"
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 2
        assert connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='index' AND name='idx_audit_entity'"
        ).fetchone()
    finally:
        connection.close()


def test_failed_migration_is_atomic_and_not_marked(tmp_path):
    folder = tmp_path / "migration"
    folder.mkdir()
    (folder / "001_bad.sql").write_text("CREATE TABLE sample(id INTEGER);\nINVALID SQL;\n")
    connection = sqlite3.connect(":memory:")
    try:
        with pytest.raises(sqlite3.OperationalError):
            migrate(connection, folder)
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 0
        assert (
            connection.execute("SELECT name FROM sqlite_master WHERE name='sample'").fetchone()
            is None
        )
    finally:
        connection.close()


def test_cli_admin_and_demo(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert (
        runner.invoke(args=["create-admin", "--username", "novo", "--password", "short"]).exit_code
        != 0
    )
    created = runner.invoke(
        args=["create-admin", "--username", "novo", "--password", "long-password-123"]
    )
    assert created.exit_code == 0
    assert (
        runner.invoke(
            args=["create-admin", "--username", "novo", "--password", "long-password-123"]
        ).exit_code
        != 0
    )
    assert runner.invoke(args=["seed-demo", "--username", "missing"]).exit_code != 0
    for _ in range(2):
        assert runner.invoke(args=["seed-demo", "--username", "novo"]).exit_code == 0
    with app.app_context():
        assert get_db().execute("SELECT count(*) FROM materials").fetchone()[0] == 4
        assert get_db().execute("SELECT count(*) FROM locations").fetchone()[0] == 2
        assert get_db().execute("SELECT count(*) FROM audit_events").fetchone()[0] == 6
