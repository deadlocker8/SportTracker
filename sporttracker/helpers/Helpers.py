from urllib.parse import urlsplit

import flask_babel


def format_duration(value: int | None) -> str:
    if value is None:
        return '--:--'

    hours = value // 3600
    minutes = value % 3600 // 60

    return f'{hours}:{str(minutes).zfill(2)}'


def format_decimal(value: int | float | None, decimals: int = 1) -> str:
    format_string = f'#,##0.{"#" * (decimals - 1)}0'
    return flask_babel.format_decimal(value, format=format_string)


def is_allowed_redirect_url(url: str | None, allowedHost: str) -> bool:
    if url is None:
        return False

    url = url.strip()
    if not url:
        return False

    urlParts = urlsplit(url)
    if urlParts.scheme not in ['', 'http', 'https']:
        return False

    return urlParts.netloc == allowedHost
