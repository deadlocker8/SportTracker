from sporttracker.logic.model.filterStates.TileHuntingFilterState import TileHuntingFilterState


class TestTileHuntingFilterState:
    def test_reset(self) -> None:
        tileHuntingFilterState = TileHuntingFilterState()
        tileHuntingFilterState.is_show_tiles_active = False  # type: ignore[assignment]
        tileHuntingFilterState.is_show_grid_active = False  # type: ignore[assignment]
        tileHuntingFilterState.is_only_highlight_new_tiles_active = False  # type: ignore[assignment]
        tileHuntingFilterState.is_show_max_square_active = False  # type: ignore[assignment]

        assert tileHuntingFilterState.is_show_tiles_active is False
        assert tileHuntingFilterState.is_show_grid_active is False
        assert tileHuntingFilterState.is_only_highlight_new_tiles_active is False
        assert tileHuntingFilterState.is_show_max_square_active is False

        tileHuntingFilterState.reset()

        assert tileHuntingFilterState.is_show_tiles_active is True
        assert tileHuntingFilterState.is_show_grid_active is True
        assert tileHuntingFilterState.is_only_highlight_new_tiles_active is True
        assert tileHuntingFilterState.is_show_max_square_active is True
