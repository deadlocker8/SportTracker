from typing import Any


class SettingsChecker:
    EXPECTED_SETTNGS = {
        'server': ['listen', 'port', 'secret', 'useSSL', 'keyfile', 'certfile'],
        'logging': ['enableRotatingLogFile', 'fileName', 'maxBytes', 'numberOfBackups'],
        'database': ['uri'],
        'gpxPreviewImages': ['enabled', 'geoRenderUrl'],
        'tileHunting': ['baseZoomLevel', 'baseZoomLevel'],
    }

    def __init__(self, settings: dict[str, Any]) -> None:
        self._settings = settings

    def check(self) -> None:
        for key, value in self.EXPECTED_SETTNGS.items():
            if key not in self._settings:
                raise KeyError(f'Invalid settings.json: Missing settings category "{key}"')

            for subKey in value:
                if subKey not in self._settings[key]:
                    raise KeyError(
                        f'Invalid settings.json: Missing settings option "{subKey}" in category "{key}"'
                    )
