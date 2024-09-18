"""gpx folder changes

Revision ID: 4439c9dfc7c7
Revises: 852bd10a0273
Create Date: 2024-09-18 22:19:08.894849

"""

import logging
import os
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

from alembic import op
from sqlalchemy import text

from sporttracker.logic import Constants

# revision identifiers, used by Alembic.
revision = '4439c9dfc7c7'
down_revision = '852bd10a0273'
branch_labels = None
depends_on = None

LOGGER = logging.getLogger(Constants.APP_NAME)


def upgrade():
    currentDirectory = os.path.abspath(os.path.dirname(__file__))
    rootDirectory = os.path.dirname(os.path.dirname(os.path.dirname(currentDirectory)))
    uploadDirectory = os.path.join(rootDirectory, 'uploads')
    dataDirectory = os.path.join(rootDirectory, 'data')

    LOGGER.debug(f'Create new data directory: "{dataDirectory}"')
    os.makedirs(dataDirectory, exist_ok=True)

    connection = op.get_bind()
    rows = connection.execute(text('SELECT "gpx_file_name" from gpx_metadata;')).fetchall()

    for index, row in enumerate(rows):
        gpxFileName = row[0]

        try:
            if gpxFileName.endswith('.gpx'):
                LOGGER.debug(
                    f'Migrate gpx data [{index + 1}/{len(rows)}]: gpx file name: "{gpxFileName}"'
                )

                gpxFileNameWithoutExtension = gpxFileName[:-4]

                connection.execute(
                    text(
                        f"UPDATE gpx_metadata SET gpx_file_name='{gpxFileNameWithoutExtension}' WHERE gpx_file_name='{gpxFileName}';"
                    )
                )
                connection.commit()
            else:
                continue

            destinationFolderPath = os.path.join(dataDirectory, gpxFileNameWithoutExtension)
            LOGGER.debug(f'    Create gpx folder: "{destinationFolderPath}"')
            os.makedirs(destinationFolderPath, exist_ok=True)

            zipFolderPath = os.path.join(
                destinationFolderPath, f'{gpxFileNameWithoutExtension}.gpx.zip'
            )
            sourceGpxPath = os.path.join(uploadDirectory, f'{gpxFileNameWithoutExtension}.gpx')

            LOGGER.debug(f'    Create gpx zip: "{zipFolderPath}"')
            with ZipFile(
                zipFolderPath, mode='w', compression=ZIP_DEFLATED, compresslevel=9
            ) as zipObject:
                zipObject.write(sourceGpxPath, arcname=gpxFileName)

            sourcePreviewImage = os.path.join(uploadDirectory, f'{gpxFileNameWithoutExtension}.jpg')
            if os.path.isfile(sourcePreviewImage):
                LOGGER.debug(f'    Move gpx preview image: "{zipFolderPath}"')
                shutil.move(sourcePreviewImage, destinationFolderPath)

            LOGGER.debug(f'    Delete old gpx  "{sourceGpxPath}"')
            os.remove(sourceGpxPath)
        except Exception:
            LOGGER.exception(f'Error migrating gpx file: "{gpxFileName}"')


def downgrade():
    pass
