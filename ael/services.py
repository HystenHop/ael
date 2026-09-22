import json
import re
import sqlite3

from .db import get_db

CATEGORIES = ("EPI", "Ferramentas", "Consumíveis", "Peças", "Outros")
UNITS = ("UN", "PAR", "CX", "KG", "L", "M")
KINDS = ("materials", "locations")


class ValidationError(ValueError):
    pass


def validate(kind, data):
    if kind not in KINDS:
        raise ValidationError("Tipo de cadastro inválido.")
    values = {"name": data.get("name", "").strip(), "code": data.get("code", "").strip().upper()}
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{1,29}", values["code"]):
        raise ValidationError("Código: use de 2 a 30 letras, números, ponto, hífen ou sublinhado.")
    if not 2 <= len(values["name"]) <= 100:
        raise ValidationError("O nome deve ter entre 2 e 100 caracteres.")
    if kind == "materials":
        values.update(category=data.get("category", ""), unit=data.get("unit", ""))
        if values["category"] not in CATEGORIES or values["unit"] not in UNITS:
            raise ValidationError("Selecione uma categoria e uma unidade válidas.")
    else:
        values["address"] = data.get("address", "").strip()
        if not 2 <= len(values["address"]) <= 160:
            raise ValidationError("O endereço deve ter entre 2 e 160 caracteres.")
    return values


def audit(connection, actor_id, kind, record_id, action, before, after):
    connection.execute(
        "INSERT INTO audit_events(actor_id, entity, entity_id, action, before_json, after_json) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            actor_id,
            kind,
            record_id,
            action,
            json.dumps(dict(before), ensure_ascii=False) if before else None,
            json.dumps(dict(after), ensure_ascii=False),
        ),
    )


def save_record(kind, data, actor_id, record_id=None):
    values = validate(kind, data)
    connection = get_db()
    try:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            before = None
            if record_id is None:
                columns = ", ".join(values)
                marks = ", ".join("?" for _ in values)
                cursor = connection.execute(
                    f"INSERT INTO {kind} ({columns}) VALUES ({marks})", tuple(values.values())
                )
                record_id = cursor.lastrowid
            else:
                before = connection.execute(
                    f"SELECT * FROM {kind} WHERE id = ?", (record_id,)
                ).fetchone()
                if before is None:
                    raise ValidationError("Cadastro não encontrado.")
                if str(before["version"]) != data.get("version"):
                    raise ValidationError("Este cadastro mudou. Reabra a página antes de editar.")
                if values["code"] != before["code"]:
                    raise ValidationError("O código não pode ser alterado nesta versão.")
                assignments = ", ".join(f"{key} = ?" for key in values)
                connection.execute(
                    f"UPDATE {kind} SET {assignments}, version = version + 1, "
                    "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (*values.values(), record_id),
                )
            after = connection.execute(
                f"SELECT * FROM {kind} WHERE id = ?", (record_id,)
            ).fetchone()
            audit(
                connection,
                actor_id,
                kind,
                record_id,
                "update" if before else "create",
                before,
                after,
            )
    except sqlite3.IntegrityError as error:
        raise ValidationError(
            "Não foi possível salvar. Verifique se o código já existe."
        ) from error
    return record_id


def set_active(kind, record_id, active, version, actor_id):
    if kind not in KINDS or active not in (0, 1):
        raise ValidationError("Operação inválida.")
    connection = get_db()
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        before = connection.execute(f"SELECT * FROM {kind} WHERE id = ?", (record_id,)).fetchone()
        if before is None:
            raise ValidationError("Cadastro não encontrado.")
        if str(before["version"]) != version:
            raise ValidationError("Este cadastro mudou. Atualize a página.")
        if before["active"] == active:
            return
        connection.execute(
            f"UPDATE {kind} SET active = ?, version = version + 1, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (active, record_id),
        )
        after = connection.execute(f"SELECT * FROM {kind} WHERE id = ?", (record_id,)).fetchone()
        audit(
            connection,
            actor_id,
            kind,
            record_id,
            "reactivate" if active else "deactivate",
            before,
            after,
        )


def seed_examples(username):
    connection = get_db()
    user = connection.execute(
        "SELECT id FROM users WHERE username = ? AND role = 'admin' AND active = 1", (username,)
    ).fetchone()
    if user is None:
        raise ValidationError("Crie primeiro um administrador ativo com esse nome.")
    records = {
        "materials": [
            dict(code="EPI-001", name="Luva de proteção mecânica", category="EPI", unit="PAR"),
            dict(code="FER-001", name="Chave combinada 13 mm", category="Ferramentas", unit="UN"),
            dict(code="CON-001", name="Fita isolante 20 m", category="Consumíveis", unit="UN"),
            dict(code="PEC-001", name="Parafuso sextavado M10", category="Peças", unit="UN"),
        ],
        "locations": [
            dict(
                code="BASE-A01",
                name="Prateleira de EPI",
                address="Base fictícia • corredor A / estante 01",
            ),
            dict(
                code="BASE-B01",
                name="Armário de ferramentas",
                address="Base fictícia • corredor B / armário 01",
            ),
        ],
    }
    for kind, rows in records.items():
        for data in rows:
            exists = connection.execute(
                f"SELECT 1 FROM {kind} WHERE code = ?", (data["code"],)
            ).fetchone()
            if not exists:
                save_record(kind, data, user["id"])
