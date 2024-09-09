import logging
import math

from PIL import Image, ImageColor

from sporttracker.logic import Constants
from sporttracker.logic.VisitedTileService import VisitedTileService, TileColorPosition

LOGGER = logging.getLogger(Constants.APP_NAME)


class TileRenderService:
    COLOR_TRANSPARENT = (0, 0, 0, 0)
    COLOR_MULTIPLE_MATCHES = (255, 0, 0, 96)

    def __init__(self, baseZoomLevel: int, tileSize: int, visitedTileService: VisitedTileService):
        self._baseZoomLevel = baseZoomLevel
        self._tileSize = tileSize
        self._visitedTileService = visitedTileService

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
        x: int, y: int, tileColorPositions: list[TileColorPosition]
    ) -> tuple[int, int, int, int]:
        """
        Calculates the color of a tile with the position (x, y).
        Expects x, y to be in self._baseZoomLevel coordinates.

        If a tile was not yet visited by the user, COLOR_TRANSPARENT is returned.
        If a tile was visited by exactly one gpx track, the color of the corresponding track type is returned.
        If a tile was visited by multiple gpx tracks, COLOR_MULTIPLE_MATCHES is returned.
        """
        colorsOfMatchingTracks = [t.tile_color for t in tileColorPositions if t.x == x and t.y == y]

        if len(colorsOfMatchingTracks) == 0:
            return TileRenderService.COLOR_TRANSPARENT

        if len(colorsOfMatchingTracks) == 1:
            return ImageColor.getcolor(colorsOfMatchingTracks[0], 'RGBA')  # type: ignore[return-value]

        return TileRenderService.COLOR_MULTIPLE_MATCHES

    @staticmethod
    def calculate_border_color(
        pixelX: int,
        pixelY: int,
        isTouchingUpperEdgeOfBaseZoomTile: bool,
        isTouchingLeftEdgeOfBaseZoomTile: bool,
        tileColor: tuple[int, int, int, int],
        borderColor: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int]:
        """
        Determines the color to use for the border pixels.
        """
        if pixelX == 0:
            if isTouchingUpperEdgeOfBaseZoomTile:
                return borderColor

        if pixelY == 0:
            if isTouchingLeftEdgeOfBaseZoomTile:
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
        zoomDifference = zoom - self._baseZoomLevel

        if not positions:
            raise RuntimeError(f'No positions were found for tile with coordinates x: {x}, y: {y}')

        max_x, max_y, min_x, min_y = self.__calculate_min_and_max(positions)

        tileColorPositions = (
            self._visitedTileService.determine_tile_colors_of_tracks_that_visit_tiles(
                min_x,  # type: ignore[arg-type]
                max_x,  # type: ignore[arg-type]
                min_y,  # type: ignore[arg-type]
                max_y,  # type: ignore[arg-type]
            )
        )

        for row in range(0, numberOfElementsPerAxis):
            for col in range(0, numberOfElementsPerAxis):
                elementIndex = row * numberOfElementsPerAxis + col
                position = positions[elementIndex]
                if zoomDifference > 0:
                    isTouchingUpperEdgeOfBaseZoomTile = x / 2**zoomDifference == position[0]
                    isTouchingLeftEdgeOfBaseZoomTile = y / 2**zoomDifference == position[1]
                else:
                    isTouchingUpperEdgeOfBaseZoomTile = True
                    isTouchingLeftEdgeOfBaseZoomTile = True

                colorToUse = self.calculate_color(position[0], position[1], tileColorPositions)

                for pixelX in range(boxSize):
                    for pixelY in range(boxSize):
                        pixels[row * boxSize + pixelX, col * boxSize + pixelY] = colorToUse  # type: ignore[index]
                        if borderColor is not None:
                            border = self.calculate_border_color(
                                pixelX,
                                pixelY,
                                isTouchingUpperEdgeOfBaseZoomTile,
                                isTouchingLeftEdgeOfBaseZoomTile,
                                colorToUse,
                                borderColor,
                            )
                            pixels[row * boxSize + pixelX, col * boxSize + pixelY] = border  # type: ignore[index]

        return img

    @staticmethod
    def __calculate_min_and_max(
        positions: list[tuple[int, int]],
    ) -> tuple[int | None, int | None, int | None, int | None]:
        min_x = None
        max_x = None
        min_y = None
        max_y = None

        for position in positions:
            pos_x, pos_y = position
            if min_x is None or pos_x < min_x:
                min_x = pos_x

            if max_x is None or pos_x > max_x:
                max_x = pos_x

            if min_y is None or pos_y < min_y:
                min_y = pos_y

            if max_y is None or pos_y > max_y:
                max_y = pos_y

        return max_x, max_y, min_x, min_y
