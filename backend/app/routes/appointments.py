from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Appointment
from ..validators import validate_appointment

appointments_bp = Blueprint("appointments", __name__, url_prefix="/api/appointments")


@appointments_bp.get("")
def list_appointments():
    subject = request.args.get("subject")
    status = request.args.get("status")
    query = Appointment.query.order_by(Appointment.exam_date.asc(), Appointment.timeslot.asc())
    if subject:
        query = query.filter_by(subject=subject)
    if status:
        query = query.filter_by(status=status)
    return jsonify([item.to_dict() for item in query.all()])


@appointments_bp.post("")
def create_appointment():
    payload = request.get_json() or {}
    error, exam_date = validate_appointment(payload)
    if error:
        return jsonify({"message": error}), 400

    appointment = Appointment(
        student_name=payload["studentName"].strip(),
        id_number=payload["idNumber"].strip(),
        subject=payload["subject"],
        exam_date=exam_date,
        timeslot=payload["timeslot"],
        status="已预约",
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify(appointment.to_dict()), 201


@appointments_bp.patch("/<int:appointment_id>")
def update_appointment_status(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    payload = request.get_json() or {}
    status = payload.get("status")
    if status not in ["已预约", "已确认", "已取消", "已完成"]:
        return jsonify({"message": "无效预约状态"}), 400
    appointment.status = status
    db.session.commit()
    return jsonify(appointment.to_dict())
