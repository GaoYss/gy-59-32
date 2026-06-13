from datetime import date, datetime, timedelta

from .base import BaseValidator, ValidationContext
from ..extensions import db
from ..models import Appointment, Rule


def parse_exam_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


class RequiredFieldsValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        required = ["studentName", "idNumber", "subject", "examDate", "timeslot"]
        missing = [field for field in required if not context.payload.get(field)]
        if missing:
            return f"缺少字段：{', '.join(missing)}"
        return None


class DateFormatValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        exam_date = parse_exam_date(context.payload.get("examDate"))
        if not exam_date:
            return "考试日期格式应为 YYYY-MM-DD"
        context.exam_date = exam_date
        return None


class PastDateValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        if context.exam_date < date.today():
            return "不能预约过去日期"
        return None


class SubjectEnabledValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        rule = Rule.query.filter_by(subject=context.payload["subject"]).first()
        if not rule or not rule.enabled:
            return "该科目暂未开放预约"
        context.rule = rule
        return None


class WeekendRestrictionValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        if context.exam_date.weekday() >= 5 and not context.rule.allow_weekend:
            return "该科目规则不允许周末预约"
        return None


class DailySlotsValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        daily_count = Appointment.query.filter(
            Appointment.subject == context.payload["subject"],
            Appointment.exam_date == context.exam_date,
            Appointment.status.in_(["已预约", "已确认"]),
        ).count()
        if daily_count >= context.rule.max_daily_slots:
            return "当日该科目预约名额已满"
        return None


class MinIntervalValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        earliest_date = date.today() + timedelta(days=context.rule.min_interval_days)
        if context.exam_date < earliest_date:
            return f"该科目需至少提前 {context.rule.min_interval_days} 天预约"
        return None


class DuplicateAppointmentValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        active = Appointment.query.filter(
            Appointment.id_number == context.payload["idNumber"],
            Appointment.subject == context.payload["subject"],
            Appointment.status.in_(["已预约", "已确认"]),
        ).first()
        if active:
            return "该学员已有同科目有效预约"
        return None


def build_validation_chain():
    required = RequiredFieldsValidator()
    date_format = DateFormatValidator()
    past_date = PastDateValidator()
    subject_enabled = SubjectEnabledValidator()
    weekend = WeekendRestrictionValidator()
    daily_slots = DailySlotsValidator()
    min_interval = MinIntervalValidator()
    duplicate = DuplicateAppointmentValidator()

    required.set_next(date_format)
    date_format.set_next(past_date)
    past_date.set_next(subject_enabled)
    subject_enabled.set_next(weekend)
    weekend.set_next(daily_slots)
    daily_slots.set_next(min_interval)
    min_interval.set_next(duplicate)

    return required


def validate_appointment(payload):
    context = ValidationContext(payload=payload)
    chain = build_validation_chain()
    error = chain.validate(context)
    return error, context.exam_date
