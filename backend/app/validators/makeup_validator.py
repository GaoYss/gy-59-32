from datetime import date, datetime

from .base import BaseValidator, ValidationContext
from ..constants import MAKEUP_STATUSES
from ..models import Rule


def parse_date(value):
    if not value:
        return None
    if not isinstance(value, str):
        return "invalid"
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return "invalid"


class RequiredFieldsValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        required = ["studentName", "originalSubject", "failedScore"]
        missing = [field for field in required if context.payload.get(field) in (None, "")]
        if missing:
            return f"缺少字段：{', '.join(missing)}"
        return None


class FailedScoreValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        try:
            score = int(context.payload["failedScore"])
        except (TypeError, ValueError):
            return "不及格分数必须是数字"
        if score < 0 or score > 100:
            return "不及格分数必须在 0-100 之间"
        context.failed_score = score
        return None


class SubjectExistsValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        rule = Rule.query.filter_by(subject=context.payload["originalSubject"]).first()
        if not rule:
            return "不存在该科目"
        context.rule = rule
        return None


class DateFormatValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        if "scheduledDate" not in context.payload:
            return None
        scheduled_date = parse_date(context.payload.get("scheduledDate"))
        if scheduled_date == "invalid":
            return "补考日期格式应为 YYYY-MM-DD"
        context.scheduled_date = scheduled_date
        return None


class PastDateValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        if not context.scheduled_date:
            return None
        if context.scheduled_date < date.today():
            return "不能安排过去的日期"
        return None


class StatusValidator(BaseValidator):
    def do_validate(self, context: ValidationContext) -> str | None:
        status = context.payload.get("status")
        if status is None:
            return None
        if status not in MAKEUP_STATUSES:
            return f"无效补考状态，可选：{', '.join(MAKEUP_STATUSES)}"
        return None


def build_create_validation_chain():
    required = RequiredFieldsValidator()
    score = FailedScoreValidator()
    subject = SubjectExistsValidator()
    date_format = DateFormatValidator()
    past_date = PastDateValidator()
    status = StatusValidator()

    required.set_next(score)
    score.set_next(subject)
    subject.set_next(date_format)
    date_format.set_next(past_date)
    past_date.set_next(status)

    return required


def build_update_validation_chain():
    date_format = DateFormatValidator()
    past_date = PastDateValidator()
    status = StatusValidator()

    date_format.set_next(past_date)
    past_date.set_next(status)

    return date_format


def validate_create_makeup(payload):
    context = ValidationContext(payload=payload)
    chain = build_create_validation_chain()
    error = chain.validate(context)
    return error, context


def validate_update_makeup(payload):
    context = ValidationContext(payload=payload)
    chain = build_update_validation_chain()
    error = chain.validate(context)
    return error, context
