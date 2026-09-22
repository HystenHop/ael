"""API de materiais: sessão administrativa e CSRF compartilhados com a interface."""

from functools import wraps

from flask import Blueprint, g, jsonify, request, url_for
from flask_wtf.csrf import generate_csrf

from .db import get_db
from .services import ValidationError, save_record

bp = Blueprint("api", __name__, url_prefix="/api")
FIELDS = ("code", "name", "category", "unit")


def error_response(code, message, status):
    return jsonify(error={"code": code, "message": message}), status


def api_admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return error_response("unauthorized", "Faça login para acessar a API.", 401)
        if g.user["role"] != "admin":
            return error_response("forbidden", "Acesso restrito ao administrador.", 403)
        return view(*args, **kwargs)

    return wrapped


def serialize(row):
    result = dict(row)
    result["active"] = bool(result["active"])
    return result


@bp.get("/csrf")
@api_admin_required
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@bp.get("/materiais")
@api_admin_required
def materials():
    query = request.args.get("q", "").strip()
    status = request.args.get("status", "active")
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "20"))
    except ValueError:
        return error_response("invalid_query", "Paginação deve usar números inteiros.", 400)
    if not 1 <= page <= 1_000_000 or not 1 <= per_page <= 100:
        return error_response(
            "invalid_query", "Use page de 1 a 1000000 e per_page de 1 a 100.", 400
        )
    if len(query) > 100 or status not in ("active", "inactive", "all"):
        return error_response("invalid_query", "Pesquisa ou situação inválida.", 400)
    pattern = "%" + query.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
    where = "(name LIKE ? ESCAPE '!' OR code LIKE ? ESCAPE '!')"
    params = [pattern, pattern]
    if status != "all":
        where += " AND active = ?"
        params.append(int(status == "active"))
    connection = get_db()
    total = connection.execute("SELECT count(*) FROM materials WHERE " + where, params).fetchone()[
        0
    ]
    rows = connection.execute(
        "SELECT * FROM materials WHERE "
        + where
        + " ORDER BY name COLLATE NOCASE, id LIMIT ? OFFSET ?",
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()
    return jsonify(
        data=[serialize(row) for row in rows],
        pagination={"page": page, "per_page": per_page, "total": total},
    )


@bp.get("/materiais/<int:material_id>")
@api_admin_required
def material(material_id):
    row = get_db().execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
    if row is None:
        return error_response("not_found", "Material não encontrado.", 404)
    return jsonify(data=serialize(row))


@bp.post("/materiais")
@api_admin_required
def create_material():
    data = request.get_json()
    if not isinstance(data, dict) or set(data) != set(FIELDS):
        return error_response(
            "invalid_payload", "Envie somente code, name, category e unit em um objeto JSON.", 400
        )
    if any(not isinstance(data[field], str) for field in FIELDS):
        return error_response("invalid_payload", "Todos os campos devem ser textos.", 400)
    try:
        material_id = save_record("materials", data, g.user["id"])
    except ValidationError as error:
        if getattr(error.__cause__, "sqlite_errorname", None) == "SQLITE_CONSTRAINT_UNIQUE":
            return error_response("duplicate_code", "Já existe um material com esse código.", 409)
        return error_response("validation_error", str(error), 400)
    row = get_db().execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
    response = jsonify(data=serialize(row))
    response.status_code = 201
    response.headers["Location"] = url_for("api.material", material_id=material_id)
    return response
