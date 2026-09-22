"""Exportação de snapshots do SQLite para Power BI, sem dados de autenticação."""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import click

from .db import get_db

QUERIES = {
    "Materiais": (
        "SELECT id, code, name, category, unit, active, created_at FROM materials ORDER BY id"
    ),
    "Locais": "SELECT id, code, name, active, created_at FROM locations ORDER BY id",
    "Eventos": (
        "SELECT id, entity || ':' || entity_id AS entity_key, entity, action, "
        "substr(created_at,1,10) AS event_date, created_at FROM audit_events ORDER BY id"
    ),
}


def export_snapshot(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    connection = get_db()
    counts = {}
    # Uma única transação de leitura mantém as tabelas no mesmo instante lógico.
    with connection:
        connection.execute("BEGIN")
        for name, query in QUERIES.items():
            cursor = connection.execute(query)
            rows = cursor.fetchall()
            with (destination / f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow([column[0] for column in cursor.description])
                writer.writerows(rows)
            counts[name] = len(rows)
    (destination / "manifest.json").write_text(
        json.dumps(
            {
                "exported_at_utc": datetime.now(UTC).isoformat(),
                "rows": counts,
                "scope": "Cadastro e auditoria; não representa saldo ou movimentação de estoque.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return counts


def init_app(app):
    @app.cli.command("export-bi")
    @click.option("--output", required=True, type=click.Path(path_type=Path))
    def export_bi(output):
        """Export a new snapshot folder for Power BI; never overwrite an existing export."""
        try:
            counts = export_snapshot(output)
        except FileExistsError as error:
            raise click.ClickException(
                "A pasta já existe. Escolha uma nova pasta de exportação."
            ) from error
        click.echo(
            f"Exportação concluída: {counts}. Use essa pasta no parâmetro PastaDados do Power BI."
        )
