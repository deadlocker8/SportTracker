from sqlalchemy import Integer, Float, String
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class GpxMetadata(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gpx_file_name: Mapped[str] = mapped_column(String, nullable=True)
    length: Mapped[float] = mapped_column(Float, nullable=False)
    elevation_minimum: Mapped[int] = mapped_column(Integer, nullable=True)
    elevation_maximum: Mapped[int] = mapped_column(Integer, nullable=True)
    uphill: Mapped[int] = mapped_column(Integer, nullable=True)
    downhill: Mapped[int] = mapped_column(Integer, nullable=True)
    editor_link: Mapped[str] = mapped_column(String, nullable=True)

    def __repr__(self):
        return (
            f'GpxMetadata('
            f'id: {self.id}, '
            f'gpx_file_name: {self.gpx_file_name}, '
            f'length: {self.length}, '
            f'elevation_minimum: {self.elevation_minimum}, '
            f'elevation_maximum: {self.elevation_maximum}, '
            f'uphill: {self.uphill}, '
            f'downhill: {self.downhill}, '
            f'editor_link: {self.editor_link})'
        )
