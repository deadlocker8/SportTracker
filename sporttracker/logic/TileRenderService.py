import logging
import math

from PIL import Image

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import VisitedTile

LOGGER = logging.getLogger(Constants.APP_NAME)


class TileRenderService:
    COLOR_TRANSPARENT = (0, 0, 0, 0)
    COLOR_MULTIPLE_MATCHES = (255, 0, 0, 96)

    def __init__(self, baseZoomLevel: int, tileSize: int, visitedTiles: set[VisitedTile]):
        self._baseZoomLevel = baseZoomLevel
        self._tileSize = tileSize
        self._visitedTiles = visitedTiles

    def __transform_tile_positions_to_base_zoom_level(
        self, x: int, y: int, zoom: int
    ) -> list[tuple[int, int]]:
        """
        Returns all tile positions for a tile with the position (x, y) and the specified zoom level transformed to self._baseZoomLevel.
        """
        if zoom == self._baseZoomLevel:
            return [(x, y)]

        newPositions: set[tuple[int, int]] = set()

        def counterIncrement(zoomLevel: int) -> int:
            return zoomLevel + 1

        def counterDecrement(zoomLevel: int) -> int:
            return zoomLevel - 1

        transformerFunction = self.transform_position_zoom_in
        counterModifierFunction = counterIncrement
        if zoom > self._baseZoomLevel:
            transformerFunction = self.transform_position_zoom_out
            counterModifierFunction = counterDecrement

        positions = [(x, y)]
        while zoom != self._baseZoomLevel:
            newPositions = set()
            for position in positions:
                newPositions = newPositions.union(
                    set(transformerFunction(position[0], position[1]))
                )
            positions = list(newPositions)
            zoom = counterModifierFunction(zoom)

        return sorted(list(newPositions), key=lambda p: (p[0], p[1]))

    @staticmethod
    def transform_position_zoom_in(x: int, y: int) -> list[tuple[int, int]]:
        """
        Returns the coordinates of all sub tiles for a tile with the position (x,y).
        The coordinates are in the sub zoom level coordinate system.
        """
        return [
            (2 * x, 2 * y),
            (2 * x + 1, +2 * y),
            (2 * x, 2 * y + 1),
            (2 * x + 1, 2 * y + 1),
        ]

    @staticmethod
    def transform_position_zoom_out(x: int, y: int) -> list[tuple[int, int]]:
        """
        Returns the coordinates of all parent tiles for a tile with the position (x,y).
        The coordinates are in the parent zoom level coordinate system.
        """
        return [(x // 2, y // 2)]

    @staticmethod
    def calculate_color(
        x: int, y: int, visitedTiles: set[VisitedTile]
    ) -> tuple[int, int, int, int]:
        """
        Return all visited tiles with the position (x, y).
        Expects x, y to be in self._baseZoomLevel coordinates.
        """
        matchingTiles = [t for t in visitedTiles if t.x == x and t.y == y]
        if len(matchingTiles) == 0:
            return TileRenderService.COLOR_TRANSPARENT

        if len(matchingTiles) == 1:
            return matchingTiles[0].color

        return TileRenderService.COLOR_MULTIPLE_MATCHES

    @staticmethod
    def calculate_border_color(
        pixelX: int,
        pixelY: int,
        tileX: int,
        tileY: int,
        position: tuple[int, int],
        tileColor: tuple[int, int, int, int],
        borderColor: tuple[int, int, int, int],
        zoomDifference: int,
    ) -> tuple[int, int, int, int]:
        """
        Determines the color to use for the border pixels.
        """
        if pixelX == 0:
            if zoomDifference <= 0 or tileY / (2 * zoomDifference) == position[1]:
                return borderColor
        if pixelY == 0:
            if zoomDifference <= 0 or tileX / (2 * zoomDifference) == position[0]:
                return borderColor

        return tileColor

    def render_image(
        self,
        x: int,
        y: int,
        zoom: int,
        borderColor: tuple[int, int, int, int] | None,
    ) -> Image.Image:
        """
        Renders a tile image for a tile with the position (x,y) and the specified zoom level.
        Already visited (sub-) tiles are shown as squares using the color defined inside the visited tile isntance.
        All non visited (sub-) tiles will be transparent.
        Optionally renders a border for each sub tile.
        """
        img = Image.new('RGBA', (self._tileSize, self._tileSize))
        pixels = img.load()

        positions = self.__transform_tile_positions_to_base_zoom_level(x, y, zoom)
        numberOfElementsPerAxis = int(math.sqrt(len(positions)))
        boxSize = int(self._tileSize / numberOfElementsPerAxis)

        for row in range(0, numberOfElementsPerAxis):
            for col in range(0, numberOfElementsPerAxis):
                elementIndex = row * numberOfElementsPerAxis + col
                position = positions[elementIndex]

                colorToUse = self.calculate_color(position[0], position[1], self._visitedTiles)

                for pixelY in range(boxSize):
                    for pixelX in range(boxSize):
                        pixels[row * boxSize + pixelY, col * boxSize + pixelX] = colorToUse  # type: ignore[index]
                        if borderColor is not None:
                            border = self.calculate_border_color(
                                pixelX,
                                pixelY,
                                x,
                                y,
                                position,
                                colorToUse,
                                borderColor,
                                zoom - self._baseZoomLevel,
                            )
                            pixels[row * boxSize + pixelY, col * boxSize + pixelX] = border  # type: ignore[index]

        return img
