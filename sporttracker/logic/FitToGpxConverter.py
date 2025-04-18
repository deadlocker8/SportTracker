from dataclasses import dataclass
from datetime import datetime

import fitdecode  # type: ignore[import-untyped]
import gpxpy.gpx


@dataclass
class TrackPoint:
    latitude: float
    longitude: float
    timestamp: datetime
    altitude: float | None


class FitToGpxConverter:
    @staticmethod
    def __parse_track_point(frame: fitdecode.records.FitDataMessage) -> TrackPoint | None:
        if not frame.has_field('position_lat') or not frame.has_field('position_long'):
            return None

        latitude = frame.get_value('position_lat')
        longitude = frame.get_value('position_long')
        if latitude is None or longitude is None:
            return None

        # convert latitude and longitude from integer to degrees
        latitude = latitude / ((2**32) / 360)
        longitude = longitude / ((2**32) / 360)

        timestamp = frame.get_value('timestamp')

        altitude = None
        if frame.has_field('altitude'):
            altitude = frame.get_value('altitude')

        if frame.has_field('enhanced_altitude'):
            enhancedAltitude = frame.get_value('enhanced_altitude')

            if altitude is None and enhancedAltitude is not None:
                altitude = enhancedAltitude

        return TrackPoint(latitude=latitude, longitude=longitude, timestamp=timestamp, altitude=altitude)

    @staticmethod
    def __parse_track_points_from_fit_file(filePath: str) -> list[TrackPoint]:
        trackPoints = []
        with fitdecode.FitReader(filePath) as fit_file:
            for frame in fit_file:
                if not isinstance(frame, fitdecode.records.FitDataMessage):
                    continue

                if frame.name != 'record':
                    continue

                trackPoint = FitToGpxConverter.__parse_track_point(frame)
                if trackPoint is not None:
                    trackPoints.append(trackPoint)

        return trackPoints

    @staticmethod
    def __create_gpx(trackPoints: list[TrackPoint]) -> gpxpy.gpx.GPX:
        gpx = gpxpy.gpx.GPX()
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)

        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for point in trackPoints:
            gpxTrackPoint = gpxpy.gpx.GPXTrackPoint(
                latitude=point.latitude,
                longitude=point.longitude,
                time=point.timestamp,
                elevation=point.altitude,
            )

            gpx_segment.points.append(gpxTrackPoint)

        return gpx

    @staticmethod
    def convert_fit_to_gpx(fitFilePath: str, gpxFilePath: str) -> None:
        trackPoints = FitToGpxConverter.__parse_track_points_from_fit_file(fitFilePath)
        gpxObject = FitToGpxConverter.__create_gpx(trackPoints=trackPoints)

        with open(gpxFilePath, 'w', encoding='utf-8') as f:
            f.write(gpxObject.to_xml())
