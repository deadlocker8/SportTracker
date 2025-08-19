import logging
import math
from enum import Enum

from PIL import Image, ImageColor

from sporttracker import Constants
from sporttracker.tileHunting.VisitedTileService import VisitedTileService, TileColorPosition, TileCountPosition

LOGGER = logging.getLogger(Constants.APP_NAME)


class TileRenderColorMode(Enum):
    NUMBER_OF_WORKOUT_TYPES = 1
    NUMBER_OF_VISITS = 2


class TileRenderService:
    COLOR_TRANSPARENT = (0, 0, 0, 0)
    COLOR_PLANNED = (0, 0, 0, 85)
    COLOR_MULTIPLE_MATCHES = (255, 0, 0, 96)

    def __init__(self, baseZoomLevel: int, tileSize: int, visitedTileService: VisitedTileService):
        self._baseZoomLevel = baseZoomLevel
        self._tileSize = tileSize
        self._visitedTileService = visitedTileService

    def __transform_tile_positions_to_base_zoom_level(self, x: int, y: int, zoom: int) -> list[tuple[int, int]]:
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
                newPositions = newPositions.union(set(transformerFunction(position[0], position[1])))
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
        x: int, y: int, tileColorPositions: list[TileColorPosition], isVisitPlanned: bool
    ) -> tuple[int, int, int, int]:
        """
        Calculates the color of a tile with the position (x, y).
        Expects x, y to be in self._baseZoomLevel coordinates.

        If a tile was not yet visited by the user, COLOR_TRANSPARENT is returned.
        If a tile was not yet visited by the user but is part of a planned tour, COLOR_PLANNED is returned.
        If a tile was visited by exactly one gpx track, the color of the corresponding track type is returned.
        If a tile was visited by multiple gpx tracks, COLOR_MULTIPLE_MATCHES is returned.
        """
        colorsOfMatchingWorkouts = [t.tile_color for t in tileColorPositions if t.x == x and t.y == y]

        if len(colorsOfMatchingWorkouts) == 0:
            if isVisitPlanned:
                return TileRenderService.COLOR_PLANNED

            return TileRenderService.COLOR_TRANSPARENT

        if len(colorsOfMatchingWorkouts) == 1:
            return ImageColor.getcolor(colorsOfMatchingWorkouts[0], 'RGBA')  # type: ignore[return-value]

        return TileRenderService.COLOR_MULTIPLE_MATCHES

    @staticmethod
    def calculate_heatmap_color(
        x: int, y: int, tileCountPositions: list[TileCountPosition]
    ) -> tuple[int, int, int, int]:
        """
        Calculates the color of a tile with the position (x, y) based on the number of times the tile was visited.
        Expects x, y to be in self._baseZoomLevel coordinates.
        """
        matchingCounts = [t for t in tileCountPositions if t.x == x and t.y == y]

        if not matchingCounts:
            return TileRenderService.COLOR_TRANSPARENT

        count = matchingCounts[0].count

        if count >= 100:
            return 89, 0, 8, 192

        if count >= 50:
            return 138, 39, 6, 192

        if count >= 25:
            return 189, 101, 51, 192

        if count >= 10:
            return 210, 150, 116, 192

        if count >= 5:
            return 3, 62, 125, 192

        if count > 1:
            return 30, 111, 156, 192

        if count == 1:
            return 113, 167, 195, 192

        return TileRenderService.COLOR_TRANSPARENT

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
        user_id: int,
        tileRenderColorMode: TileRenderColorMode,
        borderColor: tuple[int, int, int, int] | None,
        maxSquareColor: tuple[int, int, int, int] | None,
    ) -> Image.Image:
        """
        Renders a tile image for a tile with the position (x,y) and the specified zoom level.
        Already visited (sub-) tiles are shown as squares using the color defined inside the visited tile instance.
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

        tileColorPositions = []
        tileCountPositions = []
        plannedTilePositions = []
        if tileRenderColorMode == TileRenderColorMode.NUMBER_OF_WORKOUT_TYPES:
            tileColorPositions = self._visitedTileService.determine_tile_colors_of_workouts_that_visit_tiles(
                min_x,  # type: ignore[arg-type]
                max_x,  # type: ignore[arg-type]
                min_y,  # type: ignore[arg-type]
                max_y,  # type: ignore[arg-type]
                user_id,
            )
            plannedTilePositions = self._visitedTileService.determine_planned_tiles(
                min_x,  # type: ignore[arg-type]
                max_x,  # type: ignore[arg-type]
                min_y,  # type: ignore[arg-type]
                max_y,  # type: ignore[arg-type]
                user_id,
            )
        else:
            tileCountPositions = self._visitedTileService.determine_number_of_visits(
                min_x,  # type: ignore[arg-type]
                max_x,  # type: ignore[arg-type]
                min_y,  # type: ignore[arg-type]
                max_y,  # type: ignore[arg-type]
                user_id,
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

                if tileRenderColorMode == TileRenderColorMode.NUMBER_OF_WORKOUT_TYPES:
                    isVisitPlanned = any([t for t in plannedTilePositions if t.x == position[0] and t.y == position[1]])
                    colorToUse = TileRenderService.calculate_color(
                        position[0], position[1], tileColorPositions, isVisitPlanned
                    )
                else:
                    colorToUse = TileRenderService.calculate_heatmap_color(position[0], position[1], tileCountPositions)

                if maxSquareColor is not None:
                    if position in self._visitedTileService.get_max_square_tile_positions():
                        colorToUse = maxSquareColor

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
