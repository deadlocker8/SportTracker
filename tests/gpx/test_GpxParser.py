import pytest

from sporttracker.gpx.GpxService import VisitedTile, GpxParser


class TestGpxParser:
    def test_convert_coordinate_to_tile_position_zoom_too_small_should_raise(self):
        with pytest.raises(ValueError):
            GpxParser.convert_coordinate_to_tile_position(0, 0, -1)

    def test_convert_coordinate_to_tile_position_zoom_too_high_should_raise(self):
        with pytest.raises(ValueError):
            GpxParser.convert_coordinate_to_tile_position(0, 0, 21)

    @pytest.mark.parametrize(
        'lat,lon,zoom,expected_x,expected_y',
        [
            pytest.param(52.514505633612394, 13.350366839947553, 10, 549, 335, id='zoom_10'),
            pytest.param(52.514505633612394, 13.350366839947553, 11, 1099, 671, id='zoom_11'),
            pytest.param(52.514505633612394, 13.350366839947553, 12, 2199, 1343, id='zoom_12'),
            pytest.param(52.514505633612394, 13.350366839947553, 13, 4399, 2686, id='zoom_13'),
            pytest.param(52.514505633612394, 13.350366839947553, 14, 8799, 5373, id='zoom_14'),
            pytest.param(52.514505633612394, 13.350366839947553, 15, 17599, 10747, id='zoom_15'),
            pytest.param(52.514505633612394, 13.350366839947553, 16, 35198, 21494, id='zoom_16'),
        ],
    )
    def test_convert_coordinate_to_tile_position_zoom_level_16(self, lat, lon, zoom, expected_x, expected_y):
        tile = GpxParser.convert_coordinate_to_tile_position(lat, lon, zoom)
        assert tile == VisitedTile(expected_x, expected_y)

    def test_tile_to_lat_lng_bounds_zoom_zero_covers_entire_world(self):
        bounds = GpxParser.tile_to_lat_lng_bounds(0, 0, 0)
        west, south, east, north = bounds
        assert west == pytest.approx(-180.0)
        assert east == pytest.approx(180.0)
        assert north == pytest.approx(85.0511287798066, abs=1e-10)
        assert south == pytest.approx(-85.0511287798066, abs=1e-10)

    def test_tile_to_lat_lng_bounds_contains_original_coordinate(self):
        lat, lon, zoom = 52.514505633612394, 13.350366839947553, 10
        tile = GpxParser.convert_coordinate_to_tile_position(lat, lon, zoom)
        bounds = GpxParser.tile_to_lat_lng_bounds(tile.x, tile.y, zoom)
        west, south, east, north = bounds
        assert west <= lon <= east
        assert south <= lat <= north

    @pytest.mark.parametrize(
        'x, y, zoom, expected_west, expected_south, expected_east, expected_north',
        [
            pytest.param(
                549,
                335,
                10,
                13.0078125,
                52.48278022207821,
                13.359375,
                52.69636107827448,
                id='berlin_zoom_10',
            ),
            pytest.param(
                0,
                0,
                1,
                -180.0,
                0.0,
                0.0,
                85.0511287798066,
                id='nw_quadrant_zoom_1',
            ),
            pytest.param(
                1,
                0,
                1,
                0.0,
                0.0,
                180.0,
                85.0511287798066,
                id='ne_quadrant_zoom_1',
            ),
        ],
    )
    def test_tile_to_lat_lng_bounds_known_values(
        self, x, y, zoom, expected_west, expected_south, expected_east, expected_north
    ):
        bounds = GpxParser.tile_to_lat_lng_bounds(x, y, zoom)
        assert bounds[0] == pytest.approx(expected_west, abs=1e-10)
        assert bounds[1] == pytest.approx(expected_south, abs=1e-10)
        assert bounds[2] == pytest.approx(expected_east, abs=1e-10)
        assert bounds[3] == pytest.approx(expected_north, abs=1e-10)

    def test_tile_to_lat_lng_bounds_neighbor_continuity_x(self):
        bounds_left = GpxParser.tile_to_lat_lng_bounds(549, 335, 10)
        bounds_right = GpxParser.tile_to_lat_lng_bounds(550, 335, 10)
        assert bounds_left[2] == pytest.approx(bounds_right[0], abs=1e-10)

    def test_tile_to_lat_lng_bounds_neighbor_continuity_y(self):
        bounds_top = GpxParser.tile_to_lat_lng_bounds(549, 335, 10)
        bounds_bottom = GpxParser.tile_to_lat_lng_bounds(549, 336, 10)
        assert bounds_top[1] == pytest.approx(bounds_bottom[3], abs=1e-10)
