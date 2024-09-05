from PIL import Image, ImageChops

from sporttracker.logic.GpxService import VisitedTile
from sporttracker.logic.TileRenderService import TileRenderService


class TestTileRenderService:
    COLOR_NOT_VISITED = (0, 0, 0, 0)
    COLOR_VISITED = (255, 0, 0, 255)
    COLOR_BORDER = (0, 0, 0, 96)

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

    def test_calculate_color_not_visited(self):
        color = TileRenderService.calculate_color(35199, 21494, set())
        assert color == (0, 0, 0, 0)

    def test_calculate_color_visited_only_one_match(self):
        color = TileRenderService.calculate_color(
            35199, 21494, {VisitedTile(35199, 21494, self.COLOR_VISITED)}
        )
        assert color == self.COLOR_VISITED

    def test_calculate_color_visited_multiple_matches(self):
        visitedColor2 = (0, 255, 0, 255)
        visitedTiles = {
            VisitedTile(35199, 21494, self.COLOR_VISITED),
            VisitedTile(35199, 21494, visitedColor2),
        }

        color = TileRenderService.calculate_color(35199, 21494, visitedTiles)
        assert color == (255, 0, 0, 96)

    def test_calculate_border_color_not_a_border_pixel(self):
        color = TileRenderService.calculate_border_color(
            2, 2, False, False, self.COLOR_VISITED, self.COLOR_BORDER
        )
        assert color == self.COLOR_VISITED

    def test_calculate_border_color_a_border_pixel_same_zoom(self):
        color = TileRenderService.calculate_border_color(
            0, 2, True, False, self.COLOR_VISITED, self.COLOR_BORDER
        )
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
        color = TileRenderService.calculate_border_color(
            0, 2, False, False, self.COLOR_VISITED, self.COLOR_BORDER
        )
        assert color == self.COLOR_VISITED

    # type: ignore[index]
    def test_render_image_same_zoom(self):
        service = TileRenderService(
            14,
            4,
            {
                VisitedTile(35198, 21494, self.COLOR_VISITED),
                VisitedTile(35199, 21494, self.COLOR_VISITED),
            },
        )
        image = service.render_image(35198, 21494, 14, self.COLOR_BORDER)

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
        service = TileRenderService(
            14,
            4,
            {
                VisitedTile(35198, 21494, self.COLOR_VISITED),
                VisitedTile(35199, 21494, self.COLOR_VISITED),
            },
        )
        image = service.render_image(17599, 10747, 13, self.COLOR_BORDER)

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
        service = TileRenderService(13, 4, {VisitedTile(17599, 10747, self.COLOR_VISITED)})
        image = service.render_image(35198, 21494, 14, self.COLOR_BORDER)

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
