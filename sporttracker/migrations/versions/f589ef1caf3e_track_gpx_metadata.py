"""track gpx metadata

Revision ID: f589ef1caf3e
Revises: 6ac8efb50f62
Create Date: 2024-09-07 16:09:41.643033

"""

import logging
import os
from dataclasses import dataclass

import gpxpy
import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text

from sporttracker import Constants


@dataclass
class GpxMetaInfo:
    distance: float
    elevationMinimum: int | None
    elevationMaximum: int | None
    uphill: int | None
    downhill: int | None


class GpxService:
    def __init__(self, gpxPath: str) -> None:
        with open(gpxPath, encoding='utf-8') as f:
            self._gpx = gpxpy.parse(f)

    def get_meta_info(self) -> GpxMetaInfo:
        elevationExtremes = self._gpx.get_elevation_extremes()
        elevationMinimum = None
        elevationMaximum = None
        if elevationExtremes.minimum is not None and elevationExtremes.maximum is not None:
            elevationMinimum = int(elevationExtremes.minimum)
            elevationMaximum = int(elevationExtremes.maximum)

        uphillDownhill = self._gpx.get_uphill_downhill()
        uphill = None
        downhill = None
        if uphillDownhill.uphill is not None and uphillDownhill.downhill is not None:
            uphill = int(uphillDownhill.uphill)
            downhill = int(uphillDownhill.downhill)

        return GpxMetaInfo(self._gpx.length_2d(), elevationMinimum, elevationMaximum, uphill, downhill)


# revision identifiers, used by Alembic.
revision = 'f589ef1caf3e'
down_revision = '6ac8efb50f62'
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(Constants.APP_NAME)


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('track')

    columnNames = [column['name'] for column in columns]

    if 'gpx_metadata_id' not in columnNames:
        op.add_column(
            'track',
            sa.Column('gpx_metadata_id', sa.Integer(), nullable=True),
        )
        op.create_foreign_key(None, 'track', 'gpx_metadata', ['gpx_metadata_id'], ['id'])

        connection = op.get_bind()
        rows = connection.execute(
            text('SELECT "id", "gpxFileName" from track WHERE "gpxFileName" IS NOT NULL;')
        ).fetchall()

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        rootDirectory = os.path.dirname(os.path.dirname(os.path.dirname(currentDirectory)))
        uploadDirectory = os.path.join(rootDirectory, 'uploads')

        for index, row in enumerate(rows):
            gpxFileName = row[1]
            LOGGER.debug(f'Migrate track [{index + 1}/{len(rows)}]: id {row[0]} with gpx file name "{gpxFileName}"')
            gpxPath = os.path.join(uploadDirectory, gpxFileName)

            gpxService = GpxService(gpxPath)
            metaInfo = gpxService.get_meta_info()

            result = connection.execute(
                text(
                    f'INSERT INTO gpx_metadata (gpx_file_name, length, elevation_minimum, elevation_maximum, uphill, downhill) '
                    f'VALUES ('
                    f"'{gpxFileName}', "
                    f"'{metaInfo.distance}', "
                    f"'{metaInfo.elevationMinimum}', "
                    f"'{metaInfo.elevationMaximum}', "
                    f"'{metaInfo.uphill}', "
                    f"'{metaInfo.downhill}' "
                    f') RETURNING id;'
                )
            )

            gpxMetadataId = result.first()[0]  # type: ignore[index]
            connection.execute(text(f'UPDATE track SET gpx_metadata_id={gpxMetadataId} WHERE id={row[0]};'))

        op.drop_column('track', 'gpxFileName')


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('track')

    if 'gpx_metadata_id' in columnNames:
        op.drop_column('track', 'gpx_metadata_id')
