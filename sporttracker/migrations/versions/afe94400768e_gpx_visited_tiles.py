"""gpx visited tiles

Revision ID: afe94400768e
Revises: d9a71f2fcbe1
Create Date: 2024-09-07 20:19:28.995606

"""

import json
import logging
import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService

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
        rows = connection.execute(
            text(
                'SELECT t.id, g.gpx_file_name from track as t, gpx_metadata as g '
                'WHERE g.id=t.gpx_metadata_id;'
            )
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
                f'Calculate visited tiles for track {trackId} with gpx file "{gpxFileName}"'
            )
            gpxPath = os.path.join(uploadDirectory, gpxFileName)

            gpxService = GpxService(gpxPath)
            visitedTiles = gpxService.get_visited_tiles(settings['tileHunting']['baseZoomLevel'])

            for tile in visitedTiles:
                connection.execute(
                    text(
                        f'INSERT INTO gpx_visited_tile(track_id, x, y) '
                        f'VALUES ('
                        f"'{trackId}', "
                        f"'{tile.x}', "
                        f"'{tile.y}'"
                        f');'
                    )
                )


def downgrade():
    op.drop_table('gpx_visited_tiles')
