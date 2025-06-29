from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class MaintenanceFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_maintenance'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    custom_workout_field_id = db.Column(db.Integer, db.ForeignKey('custom_workout_field.id'), nullable=True)
    custom_workout_field_value: Mapped[String] = mapped_column(String, nullable=True)

    def __repr__(self):
        return (
            f'MaintenanceFilterState('
            f'user_id: {self.user_id}, '
            f'custom_workout_field_id: {self.custom_workout_field_id}, '
            f'custom_workout_field_value: {self.custom_workout_field_value})'
        )

    def is_active(self) -> bool:
        return self.custom_workout_field_id is not None and self.custom_workout_field_value is not None


def get_maintenance_filter_state_by_user(user_id: int) -> MaintenanceFilterState:
    return MaintenanceFilterState.query.filter(MaintenanceFilterState.user_id == user_id).first()
