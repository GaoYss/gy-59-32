from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class ValidationContext:
    payload: dict
    exam_date: Optional[date] = None
    errors: list = field(default_factory=list)


class BaseValidator(ABC):
    def __init__(self, next_validator=None):
        self.next_validator = next_validator

    def set_next(self, validator):
        self.next_validator = validator
        return validator

    def validate(self, context: ValidationContext) -> Optional[str]:
        error = self.do_validate(context)
        if error:
            return error
        if self.next_validator:
            return self.next_validator.validate(context)
        return None

    @abstractmethod
    def do_validate(self, context: ValidationContext) -> Optional[str]:
        pass
