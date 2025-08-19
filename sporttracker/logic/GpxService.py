from __future__ import annotations

import logging
import math
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED

import gpxpy
from gpxpy.gpx import GPX, GPXTrack, GPXTrackPoint
from sqlalchemy import delete
from werkzeug.datastructures.file_storage import FileStorage

from sporttracker.logic import Constants
from sporttracker.logic.FitToGpxConverter import FitToGpxConverter
from sporttracker.logic.GpxPreviewImageService import GpxPreviewImageService
from sporttracker.workout.distance.DistanceWorkoutEntity import DistanceWorkout
from sporttracker.logic.model.GpxMetadata import GpxMetadata
from sporttracker.logic.model.GpxPlannedTile import GpxPlannedTile
from sporttracker.logic.model.GpxVisitedTile import GpxVisitedTile
from sporttracker.plannedTour.PlannedTourEntity import PlannedTour
from sporttracker.logic.model.db import db
from sporttracker.logic.tileHunting.MaxSquareCache import MaxSquareCache
from sporttracker.logic.tileHunting.NewVisitedTileCache import NewVisitedTileCache

LOGGER = logging.getLogger(Constants.APP_NAME)


@dataclass
class ElevationExtremes:
    minimum: int | None
    maximum: int | None


@dataclass
class UphillDownhill:
    uphill: int | None
    downhill: int | None


@dataclass(frozen=True)
class VisitedTile:
    x: int
    y: int


@dataclass
class GpxMetaInfo:
    distance: float
    elevationExtremes: ElevationExtremes
    uphillDownhill: UphillDownhill
    editorLink: str | None


class GpxService:
    ZIP_FILE_EXTENSION = 'gpx.zip'
    GPX_FILE_EXTENSION = 'gpx'
    FIT_FILE_EXTENSION = 'fit'

    def __init__(
        self,
        dataPath: str,
        newVisitedTileCache: NewVisitedTileCache,
        maxSquareCache: MaxSquareCache,
    ) -> None:
        self._dataPath = dataPath
        self._newVisitedTileCache = newVisitedTileCache
        self._maxSquareCache = maxSquareCache

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

    def get_joined_tracks_and_segments(self, gpxFileName: str, downloadName: str) -> str:
        return GpxParser(self.get_gpx_content(gpxFileName)).join_tracks_and_segments(downloadName)

    def handle_gpx_upload_for_workout(self, files: dict[str, FileStorage]) -> int | None:
        gpxFileName = self.__handle_gpx_upload(
            files,
            False,
            {},
            [
                self.GPX_FILE_EXTENSION,
                self.FIT_FILE_EXTENSION,
            ],
        )
        if gpxFileName is None:
            return None

        return self.__create_gpx_metadata(gpxFileName)

    def handle_gpx_upload_for_planned_tour(
        self, files: dict[str, FileStorage], gpxPreviewImageSettings: dict[str, Any]
    ) -> int | None:
        gpxFileName = self.__handle_gpx_upload(
            files,
            gpxPreviewImageSettings['enabled'],
            gpxPreviewImageSettings,
            [
                self.GPX_FILE_EXTENSION,
                self.FIT_FILE_EXTENSION,
            ],
        )
        if gpxFileName is None:
            return None

        return self.__create_gpx_metadata(gpxFileName)

    def handle_fit_upload_for_fit_import(self, files: dict[str, FileStorage]) -> int | None:
        gpxFileName = self.__handle_gpx_upload(
            files,
            False,
            {},
            [
                self.FIT_FILE_EXTENSION,
            ],
        )
        if gpxFileName is None:
            return None

        return self.__create_gpx_metadata(gpxFileName)

    def __handle_gpx_upload(
        self,
        files: dict[str, FileStorage],
        generatePreviewImage: bool,
        gpxPreviewImageSettings: dict[str, Any],
        allowedFileExtensions: list[str],
    ) -> str | None:
        if 'gpxTrack' not in files:
            return None

        file = files['gpxTrack']
        if file.filename == '' or file.filename is None:
            return None

        if file and self.is_allowed_file(file.filename, allowedFileExtensions):
            filename = uuid.uuid4().hex
            destinationFolderPath = os.path.join(self._dataPath, filename)
            os.makedirs(destinationFolderPath)

            if file.filename.endswith(f'.{self.GPX_FILE_EXTENSION}'):
                zipFilePath = self.create_zip(filename, file.stream.read())
                LOGGER.debug(f'Saved uploaded gpx file "{file.filename}" to "{zipFilePath}"')
            elif file.filename.endswith(f'.{self.FIT_FILE_EXTENSION}'):
                self.__handle_fit_upload(destinationFolderPath, file, filename)

            if generatePreviewImage:
                gpxPreviewImageService = GpxPreviewImageService(filename, self)
                gpxPreviewImagePath = gpxPreviewImageService.get_preview_image_path()
                gpxPreviewImageService.generate_image(gpxPreviewImageSettings)
                LOGGER.debug(f'Generated gpx preview image {gpxPreviewImagePath}')

            return filename

        return None

    def __handle_fit_upload(self, destinationFolderPath: str, file: FileStorage, filename: str):
        fitFilePath = os.path.join(destinationFolderPath, f'{filename}.{self.FIT_FILE_EXTENSION}')
        file.save(fitFilePath)
        LOGGER.debug(f'Saved uploaded fit file "{file.filename}" to "{fitFilePath}"')

        gpxFilePath = os.path.join(destinationFolderPath, f'{filename}.{self.GPX_FILE_EXTENSION}')
        try:
            FitToGpxConverter.convert_fit_to_gpx(fitFilePath, gpxFilePath)

            with open(gpxFilePath, 'rb') as gpxFile:
                self.create_zip(filename, gpxFile.read())

            os.remove(gpxFilePath)
            LOGGER.debug(f'Converted uploaded fit file "{file.filename}" to gpx')
        except Exception as e:
            LOGGER.error(f'Error while converting {fitFilePath} to gpx', e)

    @staticmethod
    def is_allowed_file(filename: str, allowedFileExtensions: list[str]) -> bool:
        if '.' not in filename:
            return False

        return filename.rsplit('.', 1)[1].lower() in allowedFileExtensions

    def create_zip(self, gpxFileName: str, data: bytes) -> str:
        destinationFolderPath = os.path.join(self._dataPath, gpxFileName)
        os.makedirs(destinationFolderPath, exist_ok=True)

        zipFilePath = self.__get_zip_file_path(gpxFileName)
        with ZipFile(zipFilePath, mode='w', compression=ZIP_DEFLATED, compresslevel=9) as zipObject:
            zipObject.writestr(f'{gpxFileName}.{self.GPX_FILE_EXTENSION}', data)
        return zipFilePath

    def __create_gpx_metadata(self, gpxFileName: str) -> int:
        gpxParser = GpxParser(self.get_gpx_content(gpxFileName))
        metaInfo = gpxParser.get_meta_info()

        gpxMetadata = GpxMetadata(
            gpx_file_name=gpxFileName,
            length=metaInfo.distance,
            elevation_minimum=metaInfo.elevationExtremes.minimum,
            elevation_maximum=metaInfo.elevationExtremes.maximum,
            uphill=metaInfo.uphillDownhill.uphill,
            downhill=metaInfo.uphillDownhill.downhill,
            editor_link=metaInfo.editorLink,
        )

        db.session.add(gpxMetadata)
        db.session.commit()
        LOGGER.debug(f'Saved new GpxMetadata: {gpxMetadata}')

        return gpxMetadata.id

    def delete_gpx(self, item: DistanceWorkout | PlannedTour, userId: int) -> None:
        gpxMetadata = item.get_gpx_metadata()
        if gpxMetadata is not None:
            item.gpx_metadata_id = None
            db.session.delete(gpxMetadata)
            LOGGER.debug(f'Deleted gpx metadata {gpxMetadata.id}')
            db.session.commit()

            if isinstance(item, DistanceWorkout):
                db.session.execute(delete(GpxVisitedTile).where(GpxVisitedTile.workout_id == item.id))
                LOGGER.debug(f'Deleted gpx visited tiles for workout with id {item.id}')
                db.session.commit()

                self._newVisitedTileCache.invalidate_cache_entry_by_user(userId)
                self._maxSquareCache.invalidate_cache_entry_by_user(userId)
            else:
                db.session.execute(delete(GpxPlannedTile).where(GpxPlannedTile.planned_tour_id == item.id))
                LOGGER.debug(f'Deleted gpx planned tiles for planned tour with id {item.id}')
                db.session.commit()

            try:
                shutil.rmtree(self.get_folder_path(gpxMetadata.gpx_file_name))
                LOGGER.debug(
                    f'Deleted all files for gpx "{gpxMetadata.gpx_file_name}" for {item.__class__.__name__} id {item.id}'
                )
            except OSError as e:
                LOGGER.error(e)

    def add_visited_tiles_for_workout(self, workout: DistanceWorkout, baseZoomLevel: int, userId: int):
        visitedTiles = self.get_visited_tiles(workout.get_gpx_metadata().gpx_file_name, baseZoomLevel)  # type: ignore[union-attr]

        for tile in visitedTiles:
            gpxVisitedTile = GpxVisitedTile(workout_id=workout.id, x=tile.x, y=tile.y)
            db.session.add(gpxVisitedTile)
            db.session.commit()

        self._newVisitedTileCache.invalidate_cache_entry_by_user(userId)
        self._maxSquareCache.invalidate_cache_entry_by_user(userId)

    def add_planned_tiles_for_planned_tour(self, plannedTour: PlannedTour, baseZoomLevel: int, userId: int):
        visitedTiles = self.get_visited_tiles(plannedTour.get_gpx_metadata().gpx_file_name, baseZoomLevel)  # type: ignore[union-attr]

        for tile in visitedTiles:
            gpxPlannedTile = GpxPlannedTile(planned_tour_id=plannedTour.id, x=tile.x, y=tile.y)
            db.session.add(gpxPlannedTile)
            db.session.commit()

    def get_visited_tiles(self, gpxFileName: str, baseZoomLevel: int) -> list[VisitedTile]:
        gpxParser = GpxParser(self.get_gpx_content(gpxFileName))  # type: ignore[union-attr]
        return list(gpxParser.get_visited_tiles(baseZoomLevel))

    def has_fit_file(self, gpxFileName: str | None) -> bool:
        if gpxFileName is None:
            return False

        fitFilePath = os.path.join(self.get_folder_path(gpxFileName), f'{gpxFileName}.{self.FIT_FILE_EXTENSION}')

        return os.path.exists(fitFilePath)

    def get_fit_content(self, gpxFileName: str) -> bytes:
        if gpxFileName is None:
            raise FileNotFoundError(gpxFileName)

        fitFilePath = os.path.join(self.get_folder_path(gpxFileName), f'{gpxFileName}.{self.FIT_FILE_EXTENSION}')

        if not os.path.exists(fitFilePath):
            raise FileNotFoundError(fitFilePath)

        with open(fitFilePath, 'rb') as f:
            return f.read()

    def join_multiple_gpx(self, gpxFileNames: list[str]) -> bytes:
        joinedGpx = gpxpy.gpx.GPX()
        joinedTrack = gpxpy.gpx.GPXTrack()

        for gpxFileName in gpxFileNames:
            gpxParser = GpxParser(self.get_gpx_content(gpxFileName))
            joinedGpx.nsmap.update(gpxParser.get_namespaces())

            for segment in gpxParser.get_joined_track().segments:
                joinedTrack.segments.append(segment)

        joinedGpx.tracks.append(joinedTrack)
        return joinedGpx.to_xml(prettyprint=False).encode('utf-8')


class GpxParser:
    def __init__(self, gpxContent: bytes) -> None:
        self._gpx = self.__parse_gpx(gpxContent)

    @staticmethod
    def from_file_path(gpxFilePath: str) -> GpxParser:
        LOGGER.debug(f'Parse gpx "{gpxFilePath}"')
        with open(gpxFilePath, mode='rb', encoding='utf-8') as f:
            gpxContent = f.read()

        return GpxParser(gpxContent)

    @staticmethod
    def __parse_gpx(gpxContent: bytes) -> GPX:
        return gpxpy.parse(gpxContent)

    def join_tracks_and_segments(self, downloadName: str) -> str:
        self.__join_tracks(self._gpx)

        self.__fix_missing_elevation_for_first_points(self._gpx)

        self._gpx.name = downloadName

        return self._gpx.to_xml(prettyprint=False)

    def get_joined_track(self) -> GPXTrack:
        return self.__join_tracks(self._gpx)

    def get_namespaces(self) -> dict[str, str]:
        return self._gpx.nsmap

    @staticmethod
    def __fix_missing_elevation_for_first_points(gpx: GPX):
        if gpx.get_points_no() == 0:
            return

        # only safe if the gpx tracks and segments were joined before
        points = gpx.tracks[0].segments[0].points

        indexFirstElevation = GpxParser.__find_index_of_first_point_with_elevation(points)
        if indexFirstElevation is None:
            # no elevation data in any point
            return

        if indexFirstElevation < 2:
            # at least the first or second point contains elevation data
            return

        firstElevation = points[indexFirstElevation].elevation

        distanceBetweenFirstPointAndFirstElevation = points[0].distance_2d(points[indexFirstElevation])
        LOGGER.debug(
            f'Detected missing elevation for the gpx data points 0 to {indexFirstElevation}. '
            f'First elevation is at index {indexFirstElevation} with value {firstElevation:.2f}. '
            f'Elevation will be copied for {distanceBetweenFirstPointAndFirstElevation:.2f}m.'
        )
        for index in range(0, indexFirstElevation):
            points[index].elevation = firstElevation

    @staticmethod
    def __find_index_of_first_point_with_elevation(points: list[GPXTrackPoint]) -> int | None:
        for index, point in enumerate(points):
            if point.has_elevation():
                return index

        return None

    @staticmethod
    def __join_tracks(gpx: GPX) -> GPXTrack:
        joinedTrack = gpxpy.gpx.GPXTrack()
        numberOfTracks = len(gpx.tracks)
        for track in gpx.tracks:
            joinedTrack.segments.extend(track.segments)
            joinedTrack.link = GpxParser.escape_ampersands(track.link)

        if numberOfTracks > 1:
            LOGGER.debug(f'Joined {numberOfTracks} tracks')

        gpx.tracks.clear()
        gpx.tracks.append(joinedTrack)

        GpxParser.__join_track_segments(joinedTrack)
        return joinedTrack

    @staticmethod
    def __join_track_segments(track: GPXTrack) -> None:
        joinedSegment = gpxpy.gpx.GPXTrackSegment()

        numberOfSegments = len(track.segments)
        for segment in track.segments:
            for point in segment.points:
                joinedSegment.points.append(point)

        if numberOfSegments > 1:
            LOGGER.debug(f'Joined {numberOfSegments} segments')
            track.segments.clear()
            track.segments.append(joinedSegment)

    def __get_length(self) -> float:
        return self._gpx.length_2d()

    def __get_elevation_extremes(self) -> ElevationExtremes:
        elevationExtremes = self._gpx.get_elevation_extremes()
        minimum = elevationExtremes.minimum
        maximum = elevationExtremes.maximum
        if minimum is None or maximum is None:
            return ElevationExtremes(None, None)

        return ElevationExtremes(int(minimum), int(maximum))

    def __get_uphill_downhill(self) -> UphillDownhill:
        uphillDownhill = self._gpx.get_uphill_downhill()
        uphill = uphillDownhill.uphill
        downhill = uphillDownhill.downhill
        if uphill is None or downhill is None:
            return UphillDownhill(None, None)

        return UphillDownhill(int(uphill), int(downhill))

    def __get_editor_link(self) -> str | None:
        for track in self._gpx.tracks:
            if track.link is not None and track.link:
                return track.link

        return None

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

    def get_meta_info(self) -> GpxMetaInfo:
        return GpxMetaInfo(
            self.__get_length(),
            self.__get_elevation_extremes(),
            self.__get_uphill_downhill(),
            self.__get_editor_link(),
        )

    @staticmethod
    def escape_ampersands(url):
        if url is None:
            return None

        # Match '&' that is not followed by a valid HTML entity like &amp;, &lt;, etc.
        return re.sub(r'&(?!#?\w+;)', '%26', url)
