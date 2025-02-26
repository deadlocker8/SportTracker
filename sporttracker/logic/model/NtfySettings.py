from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class NtfySettings(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    server_url: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return (
            f'NtfySettings('
            f'id: {self.id}, '
            f'username: {self.username}, '
            f'server_url: {self.server_url}, '
            f'topic: {self.topic}, '
            f'user_id: {self.user_id},)'
        )
