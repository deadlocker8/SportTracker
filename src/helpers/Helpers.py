def format_duration(value: int | None) -> str:
    if value is None:
        return '--:--'

    hours = value // 3600
    minutes = value % 3600 // 60

    return f'{hours}:{str(minutes).zfill(2)}'
