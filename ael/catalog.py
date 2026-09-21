from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .auth import admin_required
from .db import get_db
from .services import CATEGORIES, KINDS, UNITS, ValidationError, save_record, set_active

bp = Blueprint("catalog", __name__)
LABELS = {"materials": "Materiais", "locations": "Locais"}


def check_kind(kind):
    if kind not in KINDS:
        abort(404)


@bp.get("/")
@admin_required
def dashboard():
    connection = get_db()
    counts = {}
    for kind in KINDS:
        counts[kind] = connection.execute(
            f"SELECT count(*) FROM {kind} WHERE active = 1"
        ).fetchone()[0]
    recent = connection.execute(
        "SELECT e.*, u.username FROM audit_events e JOIN users u ON u.id = e.actor_id "
        "ORDER BY e.id DESC LIMIT 5"
    ).fetchall()
    return render_template("dashboard.html", counts=counts, recent=recent)


@bp.get("/catalog/<kind>")
@admin_required
def listing(kind):
    check_kind(kind)
    query = request.args.get("q", "").strip()[:100]
    status = request.args.get("status", "active")
    if status not in ("active", "inactive", "all"):
        status = "active"
    # Escape wildcard characters so the search treats user input literally.
    pattern = "%" + query.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
    sql = f"SELECT * FROM {kind} WHERE (name LIKE ? ESCAPE '!' OR code LIKE ? ESCAPE '!')"
    params = [pattern, pattern]
    if status != "all":
        sql += " AND active = ?"
        params.append(int(status == "active"))
    rows = get_db().execute(sql + " ORDER BY name COLLATE NOCASE", params).fetchall()
    return render_template(
        "listing.html", kind=kind, title=LABELS[kind], rows=rows, query=query, status=status
    )


@bp.route("/catalog/<kind>/new", methods=["GET", "POST"])
@bp.route("/catalog/<kind>/<int:record_id>/edit", methods=["GET", "POST"])
@admin_required
def edit(kind, record_id=None):
    check_kind(kind)
    record = {}
    if record_id is not None:
        record = get_db().execute(f"SELECT * FROM {kind} WHERE id = ?", (record_id,)).fetchone()
        if record is None:
            abort(404)
        record = dict(record)
    error = None
    if request.method == "POST":
        record = request.form.to_dict()
        try:
            save_record(kind, record, g.user["id"], record_id)
            flash("Cadastro salvo com sucesso.", "success")
            return redirect(url_for("catalog.listing", kind=kind))
        except ValidationError as exc:
            error = str(exc)
    return render_template(
        "edit.html",
        kind=kind,
        title=LABELS[kind],
        record=record,
        record_id=record_id,
        categories=CATEGORIES,
        units=UNITS,
        error=error,
    ), 400 if error else 200


@bp.post("/catalog/<kind>/<int:record_id>/status")
@admin_required
def change_status(kind, record_id):
    check_kind(kind)
    value = request.form.get("active")
    try:
        if value not in ("0", "1"):
            raise ValidationError("Situação inválida.")
        set_active(kind, record_id, int(value), request.form.get("version"), g.user["id"])
        flash("Situação atualizada. O histórico foi preservado.", "success")
    except ValidationError as error:
        return render_template("error.html", message=str(error)), 400
    return redirect(url_for("catalog.listing", kind=kind, status="all"))
