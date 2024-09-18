import pytest

from sporttracker.logic.GpxService import VisitedTile, GpxParser


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
    def test_convert_coordinate_to_tile_position_zoom_level_16(
        self, lat, lon, zoom, expected_x, expected_y
    ):
        tile = GpxParser.convert_coordinate_to_tile_position(lat, lon, zoom)
        assert tile == VisitedTile(expected_x, expected_y)
