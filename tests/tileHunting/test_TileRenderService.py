from unittest.mock import Mock

from PIL import Image, ImageChops
from TheCodeLabs_BaseUtils.Color import Color

from sporttracker.tileHunting.TileRenderService import TileRenderService


class TestTileRenderService:
    COLOR_NOT_VISITED = (0, 0, 0, 0)
    COLOR_VISITED = (255, 0, 0, 255)
    COLOR_VISITED_OBJECT = Color(255, 0, 0, 1.0)
    COLOR_BORDER = (0, 0, 0, 96)

    COLOR_HEATMAP_1 = Color(113, 167, 195, 0.75)
    COLOR_HEATMAP_ABOVE_1 = Color(30, 111, 156, 0.75)
    COLOR_HEATMAP_ABOVE_5 = Color(3, 62, 125, 0.75)
    COLOR_HEATMAP_ABOVE_10 = Color(210, 150, 116, 0.75)
    COLOR_HEATMAP_ABOVE_25 = Color(189, 101, 51, 0.75)
    COLOR_HEATMAP_ABOVE_50 = Color(138, 39, 6, 0.75)
    COLOR_HEATMAP_ABOVE_100 = Color(89, 0, 8, 0.75)

    def test_transform_position_zoom_in(self):
        result = TileRenderService.transform_position_zoom_in(17599, 10747)

        assert len(result) == 4
        assert (35198, 21494) in result
        assert (35199, 21494) in result
        assert (35198, 21495) in result
        assert (35199, 21495) in result

    def test_transform_position_zoom_out(self):
        result = TileRenderService.transform_position_zoom_out(35199, 21494)

        assert len(result) == 1
        assert (17599, 10747) in result

    def test_calculate_border_color_not_a_border_pixel(self):
        color = TileRenderService.calculate_border_color(2, 2, False, False, self.COLOR_VISITED, self.COLOR_BORDER)
        assert color == self.COLOR_VISITED

    def test_calculate_border_color_a_border_pixel_same_zoom(self):
        color = TileRenderService.calculate_border_color(0, 2, True, False, self.COLOR_VISITED, self.COLOR_BORDER)
        assert color == self.COLOR_BORDER

    def test_calculate_border_color_a_border_pixel_lower_zoom(self):
        color = TileRenderService.calculate_border_color(
            0,
            2,
            True,
            False,
            self.COLOR_VISITED,
            self.COLOR_BORDER,
        )
        assert color == self.COLOR_BORDER

    def test_calculate_border_color_a_border_pixel_higher_zoom_subtile_not_at_border(self):
        color = TileRenderService.calculate_border_color(0, 2, False, False, self.COLOR_VISITED, self.COLOR_BORDER)
        assert color == self.COLOR_VISITED

    def test_render_image_same_zoom(self):
        def mocked_color_method(
            min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
        ) -> dict[tuple[int, int], Color]:
            return {
                (35198, 21494): self.COLOR_VISITED_OBJECT,
                (35199, 21494): self.COLOR_VISITED_OBJECT,
            }

        visitedTileService = Mock()
        visitedTileService.determine_tile_colors_of_workouts_that_visit_tiles.side_effect = mocked_color_method
        visitedTileService.determine_planned_tiles.return_value = []

        service = TileRenderService(14, 4, visitedTileService)
        image = service.render_image(
            35198,
            21494,
            14,
            1,
            self.COLOR_BORDER,
        )

        expectedImage = Image.new('RGBA', (4, 4))
        pixels = expectedImage.load()
        pixels[0, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 1] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 2] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 3] = self.COLOR_BORDER  # type: ignore[index]
        pixels[1, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[1, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[1, 2] = self.COLOR_VISITED  # type: ignore[index]
        pixels[1, 3] = self.COLOR_VISITED  # type: ignore[index]
        pixels[2, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[2, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[2, 2] = self.COLOR_VISITED  # type: ignore[index]
        pixels[2, 3] = self.COLOR_VISITED  # type: ignore[index]
        pixels[3, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[3, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[3, 2] = self.COLOR_VISITED  # type: ignore[index]
        pixels[3, 3] = self.COLOR_VISITED  # type: ignore[index]

        assert not ImageChops.difference(image, expectedImage).getbbox()

    def test_render_image_lower_zoom(self):
        def mocked_color_method(
            min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
        ) -> dict[tuple[int, int], Color]:
            return {
                (35198, 21494): self.COLOR_VISITED_OBJECT,
                (35199, 21494): self.COLOR_VISITED_OBJECT,
            }

        visitedTileService = Mock()
        visitedTileService.determine_tile_colors_of_workouts_that_visit_tiles.side_effect = mocked_color_method
        visitedTileService.determine_planned_tiles.return_value = []

        service = TileRenderService(14, 4, visitedTileService)
        image = service.render_image(
            17599,
            10747,
            13,
            1,
            self.COLOR_BORDER,
        )

        expectedImage = Image.new('RGBA', (4, 4))
        pixels = expectedImage.load()
        pixels[0, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 1] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 2] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 3] = self.COLOR_BORDER  # type: ignore[index]
        pixels[1, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[1, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[1, 2] = self.COLOR_BORDER  # type: ignore[index]
        pixels[1, 3] = self.COLOR_NOT_VISITED  # type: ignore[index]
        pixels[2, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[2, 1] = self.COLOR_BORDER  # type: ignore[index]
        pixels[2, 2] = self.COLOR_BORDER  # type: ignore[index]
        pixels[2, 3] = self.COLOR_BORDER  # type: ignore[index]
        pixels[3, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[3, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[3, 2] = self.COLOR_BORDER  # type: ignore[index]
        pixels[3, 3] = self.COLOR_NOT_VISITED  # type: ignore[index]

        assert not ImageChops.difference(image, expectedImage).getbbox()

    def test_render_image_higher_zoom(self):
        def mocked_color_method(
            min_x: int, max_x: int, min_y: int, max_y: int, user_id: int
        ) -> dict[tuple[int, int], Color]:
            return {
                (17599, 10747): self.COLOR_VISITED_OBJECT,
            }

        visitedTileService = Mock()
        visitedTileService.determine_tile_colors_of_workouts_that_visit_tiles.side_effect = mocked_color_method
        visitedTileService.determine_planned_tiles.return_value = []

        service = TileRenderService(15, 4, visitedTileService)
        image = service.render_image(
            35198,
            21494,
            16,
            1,
            self.COLOR_BORDER,
        )

        expectedImage = Image.new('RGBA', (4, 4), color=self.COLOR_VISITED)
        pixels = expectedImage.load()
        pixels[0, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 1] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 2] = self.COLOR_BORDER  # type: ignore[index]
        pixels[0, 3] = self.COLOR_BORDER  # type: ignore[index]
        pixels[1, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[1, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[1, 2] = self.COLOR_VISITED  # type: ignore[index]
        pixels[1, 3] = self.COLOR_VISITED  # type: ignore[index]
        pixels[2, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[2, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[2, 2] = self.COLOR_VISITED  # type: ignore[index]
        pixels[2, 3] = self.COLOR_VISITED  # type: ignore[index]
        pixels[3, 0] = self.COLOR_BORDER  # type: ignore[index]
        pixels[3, 1] = self.COLOR_VISITED  # type: ignore[index]
        pixels[3, 2] = self.COLOR_VISITED  # type: ignore[index]
        pixels[3, 3] = self.COLOR_VISITED  # type: ignore[index]

        assert not ImageChops.difference(image, expectedImage).getbbox()

    def test_calculate_heatmap_color_not_visited(self):
        color = TileRenderService.calculate_heatmap_color(0)
        assert color == Color(0, 0, 0, 0.0)

    def test_calculate_heatmap_color_visited_1(self):
        color = TileRenderService.calculate_heatmap_color(1)
        assert color == self.COLOR_HEATMAP_1

    def test_calculate_heatmap_color_visited_3(self):
        color = TileRenderService.calculate_heatmap_color(3)
        assert color == self.COLOR_HEATMAP_ABOVE_1

    def test_calculate_heatmap_color_visited_5(self):
        color = TileRenderService.calculate_heatmap_color(5)
        assert color == self.COLOR_HEATMAP_ABOVE_5

    def test_calculate_heatmap_color_visited_10(self):
        color = TileRenderService.calculate_heatmap_color(10)
        assert color == self.COLOR_HEATMAP_ABOVE_10

    def test_calculate_heatmap_color_visited_25(self):
        color = TileRenderService.calculate_heatmap_color(25)
        assert color == self.COLOR_HEATMAP_ABOVE_25

    def test_calculate_heatmap_color_visited_50(self):
        color = TileRenderService.calculate_heatmap_color(50)
        assert color == self.COLOR_HEATMAP_ABOVE_50

    def test_calculate_heatmap_color_visited_100(self):
        color = TileRenderService.calculate_heatmap_color(100)
        assert color == self.COLOR_HEATMAP_ABOVE_100
