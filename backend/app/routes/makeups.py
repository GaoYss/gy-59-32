from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Makeup
from ..validators import validate_create_makeup, validate_update_makeup

makeups_bp = Blueprint("makeups", __name__, url_prefix="/api/makeups")


@makeups_bp.get("")
def list_makeups():
    status = request.args.get("status")
    query = Makeup.query.order_by(Makeup.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return jsonify([item.to_dict() for item in query.all()])


@makeups_bp.post("")
def create_makeup():
    payload = request.get_json() or {}
    error, context = validate_create_makeup(payload)
    if error:
        return jsonify({"message": error}), 400

    scheduled_date = context.scheduled_date
    if "scheduledDate" not in payload:
        scheduled_date = None

    makeup = Makeup(
        student_name=payload["studentName"].strip(),
        original_subject=payload["originalSubject"],
        failed_score=context.failed_score,
        scheduled_date=scheduled_date,
        status=payload.get("status", "待安排"),
        notes=payload.get("notes"),
    )
    db.session.add(makeup)
    db.session.commit()
    return jsonify(makeup.to_dict()), 201


@makeups_bp.patch("/<int:makeup_id>")
def update_makeup(makeup_id):
    makeup = Makeup.query.get_or_404(makeup_id)
    payload = request.get_json() or {}

    error, context = validate_update_makeup(payload)
    if error:
        return jsonify({"message": error}), 400

    if "scheduledDate" in payload:
        makeup.scheduled_date = context.scheduled_date
    if "status" in payload:
        makeup.status = payload["status"]
    if "notes" in payload:
        makeup.notes = payload["notes"]

    db.session.commit()
    return jsonify(makeup.to_dict())
