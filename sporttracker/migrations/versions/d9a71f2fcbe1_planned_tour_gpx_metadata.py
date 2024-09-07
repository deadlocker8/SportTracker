"""planned tour gpx metadata

Revision ID: d9a71f2fcbe1
Revises: f589ef1caf3e
Create Date: 2024-09-07 18:11:45.907017

"""

import logging
import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxService

# revision identifiers, used by Alembic.
revision = 'd9a71f2fcbe1'
down_revision = 'f589ef1caf3e'
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(Constants.APP_NAME)


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('planned_tour')

    columnNames = [column['name'] for column in columns]

    if 'gpx_metadata_id' not in columnNames:
        op.add_column(
            'planned_tour',
            sa.Column('gpx_metadata_id', sa.Integer(), nullable=True),
        )
        op.create_foreign_key(None, 'planned_tour', 'gpx_metadata', ['gpx_metadata_id'], ['id'])

        connection = op.get_bind()
        rows = connection.execute(
            text('SELECT "id", "gpxFileName" from planned_tour WHERE "gpxFileName" IS NOT NULL;')
        ).fetchall()

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        rootDirectory = os.path.dirname(os.path.dirname(os.path.dirname(currentDirectory)))
        uploadDirectory = os.path.join(rootDirectory, 'uploads')

        for index, row in enumerate(rows):
            gpxFileName = row[1]
            LOGGER.debug(
                f'Migrate planned tour [{index + 1}/{len(rows)}]: id {row[0]} with gpx file name "{gpxFileName}"'
            )
            gpxPath = os.path.join(uploadDirectory, gpxFileName)

            gpxService = GpxService(gpxPath, 0, (0, 0, 0, 0))
            metaInfo = gpxService.get_meta_info()

            result = connection.execute(
                text(
                    f'INSERT INTO gpx_metadata (gpx_file_name, length, elevation_minimum, elevation_maximum, uphill, downhill) '
                    f'VALUES ('
                    f"'{gpxFileName}', "
                    f"'{metaInfo.distance}', "
                    f"'{metaInfo.elevationExtremes.minimum}', "
                    f"'{metaInfo.elevationExtremes.maximum}', "
                    f"'{metaInfo.uphillDownhill.uphill}', "
                    f"'{metaInfo.uphillDownhill.downhill}' "
                    f') RETURNING id;'
                )
            )

            gpxMetadataId = result.first()[0]  # type: ignore[index]
            connection.execute(
                text(f'UPDATE planned_tour SET gpx_metadata_id={gpxMetadataId} WHERE id={row[0]};')
            )

        op.drop_column('planned_tour', 'gpxFileName')


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('planned_tour')

    if 'gpx_metadata_id' in columnNames:
        op.drop_column('planned_tour', 'gpx_metadata_id')
