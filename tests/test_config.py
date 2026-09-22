from ael import create_app


def test_database_can_be_selected_for_an_isolated_cli_run(monkeypatch, tmp_path):
    database = tmp_path / "demo.sqlite3"
    monkeypatch.setenv("AEL_DATABASE", str(database))

    app = create_app({"TESTING": True, "SECRET_KEY": "only-for-automated-tests-not-production"})

    assert app.config["DATABASE"] == str(database)
