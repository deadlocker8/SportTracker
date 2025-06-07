"""gpx_metadata_editor_link

Revision ID: f10e23ade4d8
Revises: 42608807ae69
Create Date: 2025-06-07 17:20:13.683117

"""

import logging
import os
from zipfile import ZipFile

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Inspector, text

from sporttracker.logic import Constants
from sporttracker.logic.GpxService import GpxParser


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

    def get_editor_link(self, gpxFileName: str) -> str | None:
        gpxParser = GpxParser(self.get_gpx_content(gpxFileName))
        return gpxParser.get_meta_info().editorLink


# revision identifiers, used by Alembic.
revision = 'f10e23ade4d8'
down_revision = '42608807ae69'
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(Constants.APP_NAME)


def upgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columns = inspector.get_columns('gpx_metadata')
    columnNames = [column['name'] for column in columns]

    if 'editor_link' not in columnNames:
        op.add_column(
            'gpx_metadata',
            sa.Column('editor_link', sa.String(), nullable=True),
        )

        currentDirectory = os.path.abspath(os.path.dirname(__file__))
        rootDirectory = os.path.dirname(os.path.dirname(os.path.dirname(currentDirectory)))
        dataDirectory = os.path.join(rootDirectory, 'data')

        gpxService = GpxService(dataDirectory)

        connection = op.get_bind()
        rows = connection.execute(
            text(
                'SELECT g."id", g."gpx_file_name", p."id" from gpx_metadata as g join planned_tour AS p ON g."id" = p."gpx_metadata_id" WHERE g.editor_link IS NULL;'
            )
        ).fetchall()

        for row in rows:
            try:
                editorLink = gpxService.get_editor_link(row[1])
                if editorLink is not None:
                    LOGGER.debug(f'Adding editor link for existing planned tour with ID {row[2]}')
                    op.execute(f"UPDATE gpx_metadata SET editor_link='{editorLink}' WHERE id={row[0]};")
            except Exception as e:
                LOGGER.error(e)


def downgrade():
    inspector = Inspector.from_engine(op.get_bind().engine)
    columnNames = inspector.get_columns('gpx_metadata')

    if 'editor_link' in columnNames:
        op.drop_column('gpx_metadata', 'editor_link')
