import csv
import json

from ael.bi import export_snapshot
from tests.conftest import material, submit


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def test_bi_exports_database_and_omits_secrets(app, admin, tmp_path):
    submit(admin, data=material(name='Luva; "especial"'))
    target = tmp_path / "snapshot"
    with app.app_context():
        counts = export_snapshot(target)
    assert counts == {"Materiais": 1, "Locais": 0, "Eventos": 1}
    exported = rows(target / "Materiais.csv")
    assert exported[0]["name"] == 'Luva; "especial"'
    event = rows(target / "Eventos.csv")[0]
    assert event["entity_key"] == "materials:1"
    assert event["action"] == "create"
    assert "actor_id" not in event and "after_json" not in event
    assert json.loads((target / "manifest.json").read_text())["rows"] == counts
    assert not (target / "users.csv").exists()


def test_bi_cli_preserves_existing_export(app, tmp_path):
    target = tmp_path / "snapshot"
    runner = app.test_cli_runner()
    assert runner.invoke(args=["export-bi", "--output", str(target)]).exit_code == 0
    original = (target / "manifest.json").read_bytes()
    assert runner.invoke(args=["export-bi", "--output", str(target)]).exit_code != 0
    assert (target / "manifest.json").read_bytes() == original
    assert rows(target / "Materiais.csv") == []
