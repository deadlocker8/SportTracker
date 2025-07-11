from sqlalchemy import Boolean
from sqlalchemy.orm import mapped_column, Mapped

from sporttracker.logic.model.db import db


class TileHuntingFilterState(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'filter_state_tile_hunting'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, primary_key=True)
    is_show_tiles_active: Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    is_show_grid_active: Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    is_only_highlight_new_tiles_active: Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    is_show_max_square_active: Mapped[Boolean] = mapped_column(Boolean, nullable=False)
    is_show_planned_tiles_active: Mapped[Boolean] = mapped_column(Boolean, nullable=False)

    def __repr__(self):
        return (
            f'TileHuntingFilterState('
            f'user_id: {self.user_id}, '
            f'is_show_tiles_active: {self.is_show_tiles_active}, '
            f'is_show_grid_active: {self.is_show_grid_active}, '
            f'is_only_highlight_new_tiles_active: {self.is_only_highlight_new_tiles_active}, '
            f'is_show_max_square_active: {self.is_show_max_square_active},'
            f'is_show_planned_tiles_active: {self.is_show_planned_tiles_active})'
        )

    def reset(self) -> None:
        self.is_show_tiles_active = True  # type: ignore[assignment]
        self.is_show_grid_active = True  # type: ignore[assignment]
        self.is_only_highlight_new_tiles_active = True  # type: ignore[assignment]
        self.is_show_max_square_active = True  # type: ignore[assignment]
        self.is_show_planned_tiles_active = True  # type: ignore[assignment]


def get_tile_hunting_filter_state_by_user(user_id: int) -> TileHuntingFilterState:
    return TileHuntingFilterState.query.filter(TileHuntingFilterState.user_id == user_id).first()
