from sqlalchemy import inspect, text

from .extensions import db


def run_migrations():
    inspector = inspect(db.engine)
    columns = [col["name"] for col in inspector.get_columns("rules")]

    if "max_slots_per_timeslot" not in columns:
        db.session.execute(
            text("ALTER TABLE rules ADD COLUMN max_slots_per_timeslot INTEGER NOT NULL DEFAULT 5")
        )
        db.session.commit()
