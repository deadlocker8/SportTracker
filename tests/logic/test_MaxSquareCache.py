from sporttracker.logic.tileHunting.MaxSquareCache import MaxSquareCache


class TestMaxSquareCache:
    def test_calculate_max_square_no_visited_tiles(self):
        result = MaxSquareCache._calculate_max_square([])
        assert len(result) == 0

    def test_calculate_max_square_one_visited_tile(self):
        result = MaxSquareCache._calculate_max_square([(123, 456)])
        assert len(result) == 1
        assert (123, 456) in result

    def test_calculate_max_square_2x2_square(self):
        result = MaxSquareCache._calculate_max_square(
            [
                (1, 1),
                (1, 2),
                (2, 1),
                (2, 2),
            ]
        )
        assert len(result) == 4
        assert (1, 1) in result
        assert (1, 2) in result
        assert (2, 1) in result
        assert (2, 2) in result

    def test_calculate_max_square_multiple_2x2_squares(self):
        result = MaxSquareCache._calculate_max_square(
            [
                (1, 1),
                (1, 2),
                (2, 1),
                (2, 2),
                (5, 5),
                (5, 6),
                (6, 5),
                (6, 6),
            ]
        )
        assert len(result) == 4
        assert (1, 1) in result
        assert (1, 2) in result
        assert (2, 1) in result
        assert (2, 2) in result

    def test_calculate_max_square_2x2_square_not_completely_visited(self):
        result = MaxSquareCache._calculate_max_square(
            [
                (1, 1),
                (1, 2),
                (2, 2),
            ]
        )
        assert len(result) == 1
        assert (1, 1) in result

    def test_calculate_max_square_2x2_square_in_large_mesh(self):
        result = MaxSquareCache._calculate_max_square(
            [
                (1, 1),
                (2, 1),
                (2, 2),
                (1, 3),
                (1, 4),
                (3, 2),
                (5, 5),
                (5, 6),
                (6, 5),
                (6, 6),
            ]
        )
        assert len(result) == 4
        assert (5, 5) in result
        assert (5, 6) in result
        assert (6, 5) in result
        assert (5, 6) in result
