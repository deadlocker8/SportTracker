from sporttracker.tileHunting.VisitedTileCache import VisitedTileCache


class TestVisitedTileCacheMaxSquare:
    def test_calculate_max_square_no_visited_tiles(self):
        result = VisitedTileCache._calculate_max_square([])
        assert len(result) == 0

    def test_calculate_max_square_one_visited_tile(self):
        result = VisitedTileCache._calculate_max_square([(123, 456)])
        assert len(result) == 1
        assert (123, 456) in result

    def test_calculate_max_square_2x2_square(self):
        result = VisitedTileCache._calculate_max_square(
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
        result = VisitedTileCache._calculate_max_square(
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
        result = VisitedTileCache._calculate_max_square(
            [
                (1, 1),
                (1, 2),
                (2, 2),
            ]
        )
        assert len(result) == 1
        assert (1, 1) in result

    def test_calculate_max_square_2x2_square_in_large_mesh(self):
        result = VisitedTileCache._calculate_max_square(
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


class TestVisitedTileCacheMaxCluster:
    def test_calculate_max_cluster_no_visited_tiles(self):
        result = VisitedTileCache._calculate_max_cluster([])
        assert len(result) == 0

    def test_calculate_max_cluster_one_visited_tile(self):
        result = VisitedTileCache._calculate_max_cluster([(123, 456)])
        assert len(result) == 1
        assert (123, 456) in result

    def test_calculate_max_cluster_2x2_square(self):
        result = VisitedTileCache._calculate_max_cluster(
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

    def test_calculate_max_cluster_returns_largest_of_multiple_clusters(self):
        result = VisitedTileCache._calculate_max_cluster(
            [
                (1, 1),
                (1, 2),
                (2, 1),
                (2, 2),
                (10, 10),
                (11, 10),
            ]
        )
        assert len(result) == 4
        assert (1, 1) in result
        assert (1, 2) in result
        assert (2, 1) in result
        assert (2, 2) in result

    def test_calculate_max_cluster_l_shape(self):
        result = VisitedTileCache._calculate_max_cluster(
            [
                (0, 0),
                (0, 1),
                (0, 2),
                (1, 0),
            ]
        )
        assert len(result) == 4

    def test_calculate_max_cluster_diagonal_tiles_are_not_connected(self):
        result = VisitedTileCache._calculate_max_cluster(
            [
                (0, 0),
                (1, 1),
                (2, 2),
            ]
        )
        assert len(result) == 1

    def test_calculate_max_cluster_chain_of_tiles(self):
        result = VisitedTileCache._calculate_max_cluster(
            [
                (0, 0),
                (1, 0),
                (2, 0),
                (3, 0),
                (4, 0),
            ]
        )
        assert len(result) == 5
