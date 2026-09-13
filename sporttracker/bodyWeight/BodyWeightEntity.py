from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from sporttracker.db import db
from sporttracker.helpers import DateFormats


class BodyWeight(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'body_weight'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    datetime: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)  # grams

    def get_date(self) -> str:
        return self.datetime.strftime(DateFormats.DATE_FORMAT_DATE)  # type: ignore[attr-defined]

    def get_time(self) -> str:
        return self.datetime.strftime(DateFormats.DATE_FORMAT_TIME)  # type: ignore[attr-defined]

    def __repr__(self):
        return f'BodyWeight(id: {self.id}, date: {self.datetime}, weight: {self.weight}, user_id: {self.user_id})'
