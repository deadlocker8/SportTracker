"""gpx_planned_tiles

Revision ID: 885a4670527a
Revises: e6d14acbc655
Create Date: 2025-07-11 21:50:51.661275

"""

import json
import logging
import math
import os
from dataclasses import dataclass
from zipfile import ZipFile

import gpxpy
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text

from sporttracker.logic import Constants


@dataclass(frozen=True)
class VisitedTile:
    x: int
    y: int


class GpxService:
    ZIP_FILE_EXTENSION = 'gpx.zip'
    GPX_FILE_EXTENSION = 'gpx'

    def __init__(self, dataPath: str) -> None:
        self._dataPath = dataPath

    def get_folder_path(self, gpxFileName: str) -> str:
        return os.path.join(self._dataPath, gpxFileName)

    def __get_zip_file_path(self, gpxFileName: str) -> str:
        return os.path.join(self.get_folder_path(gpxFileName), f'{gpxFileName}.{self.ZIP_FILE_EXTENSION}')

    def get_gpx_content(self, gpxFileName: str) -> bytes:
        zipFilePath = self.__get_zip_file_path(gpxFileName)

        if not os.path.exists(zipFilePath):
            raise FileNotFoundError(zipFilePath)

        with ZipFile(zipFilePath, 'r') as zipObject:
            with zipObject.open(f'{gpxFileName}.{self.GPX_FILE_EXTENSION}') as gpxFile:
                return gpxFile.read()

    def get_visited_tiles(self, gpxFileName: str, baseZoomLevel: int) -> set[VisitedTile]:
        gpx = gpxpy.parse(self.get_gpx_content(gpxFileName))

        visitedTiles = set()

        numberOfPoints = gpx.get_points_no()
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    visitedTiles.add(
                        self.convert_coordinate_to_tile_position(point.latitude, point.longitude, baseZoomLevel)
                    )

        LOGGER.debug(f'{numberOfPoints} points in gpx track resulted in {len(visitedTiles)} distinct tiles')
        return visitedTiles

    @staticmethod
    def convert_coordinate_to_tile_position(lat_deg: float, lon_deg: float, zoom: int) -> VisitedTile:
        if zoom < 0 or zoom > 20:
            raise ValueError(f'Zoom level {zoom} is not valid. Must be between 0 and 20')

        lat_rad = math.radians(lat_deg)
        n = 1 << zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return VisitedTile(x, y)


# revision identifiers, used by Alembic.
revision = '885a4670527a'
down_revision = 'e6d14acbc655'
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(Constants.APP_NAME)


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    __handle_new_table_gpx_planned_tiles(tableNames)

    columns = inspector.get_columns('filter_state_tile_hunting')
    columnNames = [column['name'] for column in columns]

    if 'is_show_planned_tiles_active' not in columnNames:
        op.add_column(
            'filter_state_tile_hunting',
            sa.Column('is_show_planned_tiles_active', sa.Boolean(), nullable=True),
        )

        connection = op.get_bind()
        connection.execute(
            text(
                'UPDATE filter_state_tile_hunting SET is_show_planned_tiles_active=True WHERE is_show_planned_tiles_active is NULL;'
            )
        )

    columns = inspector.get_columns('user')
    columnNames = [column['name'] for column in columns]
    if 'isTileHuntingShowPlannedTilesActivated' not in columnNames:
        op.add_column(
            'user',
            sa.Column('isTileHuntingShowPlannedTilesActivated', sa.Boolean(), nullable=True, default=True),
        )

    op.execute(
        'UPDATE "user" SET "isTileHuntingShowPlannedTilesActivated"=True WHERE "user"."isTileHuntingShowPlannedTilesActivated" IS NULL;'
    )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'gpx_planned_tile' not in tableNames:
        op.drop_table('gpx_planned_tile')

    columnNames = inspector.get_columns('filter_state_tile_hunting')
    if 'is_show_planned_tiles_active' in columnNames:
        op.drop_column('filter_state_tile_hunting', 'is_show_planned_tiles_active')

    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('user')
    if 'isTileHuntingShowPlannedTilesActivated' in columnNames:
        op.drop_column('user', 'isTileHuntingShowPlannedTilesActivated')


def __handle_new_table_gpx_planned_tiles(tableNames):
    if 'gpx_planned_tile' not in tableNames:
        op.create_table(
            'gpx_planned_tile',
            sa.Column('planned_tour_id', sa.Integer(), nullable=False),
            sa.Column('x', sa.Integer(), nullable=False),
            sa.Column('y', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('planned_tour_id', 'x', 'y'),
        )

    connection = op.get_bind()
    existingTableEntries = connection.execute(text('SELECT * FROM gpx_planned_tile')).fetchall()

    if len(existingTableEntries) == 0:
        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        rootDirectory = os.path.dirname(os.path.dirname(os.path.dirname(currentDirectory)))
        dataDirectory = os.path.join(rootDirectory, 'data')
        settingsPath = os.path.join(rootDirectory, 'settings.json')

        gpxService = GpxService(dataDirectory)

        with open(settingsPath, 'r', encoding='UTF-8') as f:
            settings = json.load(f)

        rows = connection.execute(
            text(
                'SELECT g."id", g."gpx_file_name", p."id" from gpx_metadata as g join planned_tour AS p ON g."id" = p."gpx_metadata_id";'
            )
        ).fetchall()

        for row in rows:
            plannedTourId = row[2]
            gpxFileName = row[1]
            LOGGER.debug(f'Calculate planned tiles for planned tour {plannedTourId} with gpx file "{gpxFileName}"')

            visitedTiles = gpxService.get_visited_tiles(gpxFileName, settings['tileHunting']['baseZoomLevel'])

            for tile in visitedTiles:
                connection.execute(
                    text(
                        f"INSERT INTO gpx_planned_tile(planned_tour_id, x, y) VALUES ('{plannedTourId}', '{tile.x}', '{tile.y}');"
                    )
                )
