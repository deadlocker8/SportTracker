from datetime import date

from sporttracker.tileHunting.NewVisitedTileCache import NewVisitedTileCache


class TestNewVisitedTileCache:
    def test_build_date_range_operators_no_filter(self):
        result = NewVisitedTileCache._build_date_range_operators(None)
        assert result == ('', '', {})

    def test_build_date_range_operators_empty_filter(self):
        result = NewVisitedTileCache._build_date_range_operators([])
        assert result == ('AND (1 = 0)', 'AND (1 = 0)', {})

    def test_build_date_range_operators_single_date_range(self):
        result = NewVisitedTileCache._build_date_range_operators([(date(2025, 6, 1), date(2025, 6, 30))])
        assert result[0] == (
            'AND (w_inner."start_time" >= :date_range_0_from AND w_inner."start_time" < :date_range_0_to)'
        )
        assert result[1] == ('AND (w."start_time" >= :date_range_0_from AND w."start_time" < :date_range_0_to)')
        assert result[2] == {
            'date_range_0_from': date(2025, 6, 1),
            'date_range_0_to': date(2025, 7, 1),
        }

    def test_build_date_range_operators_multiple_date_ranges(self):
        result = NewVisitedTileCache._build_date_range_operators(
            [
                (date(2020, 1, 1), date(2020, 12, 31)),
                (date(2022, 1, 1), date(2022, 12, 31)),
            ]
        )
        assert result[0] == (
            'AND (w_inner."start_time" >= :date_range_0_from AND w_inner."start_time" < :date_range_0_to '
            'OR w_inner."start_time" >= :date_range_1_from AND w_inner."start_time" < :date_range_1_to)'
        )
        assert result[1] == (
            'AND (w."start_time" >= :date_range_0_from AND w."start_time" < :date_range_0_to '
            'OR w."start_time" >= :date_range_1_from AND w."start_time" < :date_range_1_to)'
        )
        assert result[2] == {
            'date_range_0_from': date(2020, 1, 1),
            'date_range_0_to': date(2021, 1, 1),
            'date_range_1_from': date(2022, 1, 1),
            'date_range_1_to': date(2023, 1, 1),
        }

    def test_build_date_range_operators_end_date_inclusive(self):
        result = NewVisitedTileCache._build_date_range_operators([(date(2025, 12, 31), date(2025, 12, 31))])
        assert result[2] == {
            'date_range_0_from': date(2025, 12, 31),
            'date_range_0_to': date(2026, 1, 1),
        }
