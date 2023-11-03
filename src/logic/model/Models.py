from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    tracks = db.relationship('Track', backref='user', lazy=True)


class Track(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    startTime: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    distance: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
