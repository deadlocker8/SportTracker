import os

from PIL import ImageColor
from flask_login import current_user
from sqlalchemy import extract

from sporttracker.logic.GpxService import VisitedTile, CachedGpxService
from sporttracker.logic.QuickFilterState import QuickFilterState
from sporttracker.logic.model.Track import Track


class VisitedTileService:
    @staticmethod
    def calculate_visited_tiles(
        quickFilterState: QuickFilterState,
        yearFilterState: list[int],
        uploadFolder: str,
        cachedGpxService: CachedGpxService,
    ) -> set[VisitedTile]:
        tracks = (
            Track.query.filter(Track.user_id == current_user.id)
            .filter(Track.gpx_metadata_id.isnot(None))
            .filter(Track.type.in_(quickFilterState.get_active_types()))
            .filter(extract('year', Track.startTime).in_(yearFilterState))
            .all()
        )

        totalVisitedTiles: set[VisitedTile] = set()
        for track in tracks:
            gpxTrackPath = os.path.join(uploadFolder, track.get_gpx_metadata())
            color = ImageColor.getcolor(track.type.tile_color, 'RGBA')
            gpxMetaInfo = cachedGpxService.get_meta_info(gpxTrackPath, color)  # type: ignore[arg-type]
            totalVisitedTiles = totalVisitedTiles.union(gpxMetaInfo.visitedTiles)

        return totalVisitedTiles
