import csv
from datetime import datetime

import click
import requests
from TheCodeLabs_BaseUtils.DefaultLogger import DefaultLogger

from sporttracker.logic.model.TrackType import TrackType

LOGGER = DefaultLogger().create_logger_if_not_exists('CsvParser')


class CsvParser:
    DATE_FORMAT = '%d.%m.%Y'

    @classmethod
    def import_csv(cls, csvPath: str, session, url: str) -> None:
        LOGGER.debug(f'Parsing csv file "{csvPath}"...')

        tracks = 0
        monthGoals = 0

        lastRow = None

        with open(csvPath, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                try:
                    trackDate = datetime.strptime(row[2], cls.DATE_FORMAT)
                except ValueError:
                    continue

                hours, minutes, seconds = cls.__calculate_duration(row[7])

                if row[17] == 'Monat' and row[18] == 'Minimalziel':
                    lastRow = row

                if lastRow is not None and lastRow[17] == 'Monat' and row[18] == 'Ideal':
                    distance_minimum = cls.__calculate_distance(lastRow[19])
                    distance_perfect = cls.__calculate_distance(row[19])
                    year = 2000 + int(row[11][-2:])

                    for index in range(12):
                        goalData = {
                            'type': TrackType.BIKING.name,
                            'year': year,
                            'month': index + 1,
                            'distance_minimum': distance_minimum,
                            'distance_perfect': distance_perfect,
                        }
                        LOGGER.debug(f'Importing {goalData}')
                        response = session.post(f'{url}/api/addMonthGoalDistance', json=goalData)
                        LOGGER.debug(response.content)
                        if not response.ok:
                            raise RuntimeError(response)

                        monthGoals += 1
                        lastRow = None

                data = {
                    'name': row[5],
                    'type': TrackType.BIKING.name,
                    'date': trackDate.strftime('%Y-%m-%d'),
                    'time': '12:00',
                    'durationHours': hours,
                    'durationMinutes': minutes,
                    'durationSeconds': seconds,
                    'distance': cls.__calculate_distance(row[4]),
                    'averageHeartRate': None,
                    'customFields': {'Bike': row[9]},
                }
                LOGGER.debug(f'Importing {data}')
                response = session.post(f'{url}/api/addTrack', json=data)
                LOGGER.debug(response.content)
                if not response.ok:
                    raise RuntimeError(response)

                tracks += 1

        LOGGER.debug(f'Imported {tracks} tracks from csv')
        LOGGER.debug(f'Imported {monthGoals} month goals from csv')

    @staticmethod
    def __calculate_distance(distanceString: str) -> float:
        result = distanceString[:-3]  # remove " km" suffix
        result = result.replace(',', '.')
        return float(result)

    @staticmethod
    def __calculate_duration(durationString: str) -> tuple:
        if ':' not in durationString:
            return None, None, None

        hours, minutes, seconds = durationString.split(':')
        return int(hours), int(minutes), int(seconds)


@click.command()
@click.option('--username', '-u', help='Username', required=True)
@click.option('--password', '-p', help='Password', required=True)
@click.option('--url', '-url', help='API URL', required=True)
@click.option('--csv', '-csv', help='CSV Path', required=True)
def run(username, password, url, csv):
    LOGGER.debug('Log in...')
    session = requests.Session()
    response = session.post(f'{url}/login', data={'username': username, 'password': password})
    LOGGER.debug(response.content)
    if not response.ok:
        raise RuntimeError(response)

    LOGGER.debug('Log in DONE')

    CsvParser.import_csv(csv, session, url)


if __name__ == '__main__':
    run()
