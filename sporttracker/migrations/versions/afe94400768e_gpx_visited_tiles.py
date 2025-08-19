"""gpx visited tiles

Revision ID: afe94400768e
Revises: d9a71f2fcbe1
Create Date: 2024-09-07 20:19:28.995606

"""

import json
import logging
import math
import os
from dataclasses import dataclass

import gpxpy
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text

from sporttracker import Constants


@dataclass(frozen=True)
class VisitedTile:
    x: int
    y: int


class GpxService:
    def __init__(self, gpxPath: str) -> None:
        with open(gpxPath, encoding='utf-8') as f:
            self._gpx = gpxpy.parse(f)

    def get_visited_tiles(self, baseZoomLevel: int) -> set[VisitedTile]:
        visitedTiles = set()

        numberOfPoints = self._gpx.get_points_no()
        for track in self._gpx.tracks:
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
revision = 'afe94400768e'
down_revision = 'd9a71f2fcbe1'
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(Constants.APP_NAME)


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'gpx_visited_tile' not in tableNames:
        op.create_table(
            'gpx_visited_tile',
            sa.Column('track_id', sa.Integer(), nullable=False),
            sa.Column('x', sa.Integer(), nullable=False),
            sa.Column('y', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('track_id', 'x', 'y'),
        )

    connection = op.get_bind()
    existingTableEntries = connection.execute(text('SELECT * FROM gpx_visited_tile')).fetchall()
    if len(existingTableEntries) == 0:
        rows = connection.execute(
            text('SELECT t.id, g.gpx_file_name from track as t, gpx_metadata as g WHERE g.id=t.gpx_metadata_id;')
        ).fetchall()

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        rootDirectory = os.path.dirname(os.path.dirname(os.path.dirname(currentDirectory)))
        uploadDirectory = os.path.join(rootDirectory, 'uploads')
        settingsPath = os.path.join(rootDirectory, 'settings.json')

        with open(settingsPath, 'r', encoding='UTF-8') as f:
            settings = json.load(f)

        for index, row in enumerate(rows):
            trackId = row[0]
            gpxFileName = row[1]
            LOGGER.debug(
                f'Calculate visited tiles for track [{index + 1}/{len(rows)}]: id {trackId} with gpx file "{gpxFileName}"'
            )
            gpxPath = os.path.join(uploadDirectory, gpxFileName)

            gpxService = GpxService(gpxPath)
            visitedTiles = gpxService.get_visited_tiles(settings['tileHunting']['baseZoomLevel'])

            for tile in visitedTiles:
                connection.execute(
                    text(f"INSERT INTO gpx_visited_tile(track_id, x, y) VALUES ('{trackId}', '{tile.x}', '{tile.y}');")
                )


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    tableNames = inspector.get_table_names()

    if 'gpx_visited_tile' not in tableNames:
        op.drop_table('gpx_visited_tile')
