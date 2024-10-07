import asyncio
import logging
import os
import time

import aiohttp

from src.api_sports import APISports
from src.football_calendar import FootballCalendar, FootballCalendarEvent

SEASON = int(os.getenv('SEASON'))  # TODO: 2024
LEAGUE = os.getenv('LEAGUE')  # TODO: 253
TEAM_ID = os.getenv('TEAM_ID')  # TODO: 1615 DC UNITED
TEAM_NAME = os.getenv('TEAM_NAME')
OUTPUT_PATH = os.getenv('OUTPUT_PATH')
LOG_LEVEL = os.getenv('LOG_LEVEL')

logging.getLogger().setLevel(logging.DEBUG if LOG_LEVEL == 'DEBUG' else logging.INFO)

api_sports_client = APISports()


async def fetch_data():
    conn = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=conn) as client:
        retry = 1
        while retry < 5:
            time.sleep(1)
            async with asyncio.TaskGroup() as tg:
                future = tg.create_task(api_sports_client.get_fixtures(client, TEAM_ID, SEASON))
            fixtures = future.result()
            if len(fixtures) > 0:
                return fixtures
            else:
                logging.warning(f'Unable to fetch fixtures, attempts={retry}')
                retry += 1

    raise Exception('Unable to fetch fixtures from API provider')


def main() -> dict:
    fixtures = asyncio.run(fetch_data())
    cal = FootballCalendar.to_football_calendar(
        TEAM_NAME,
        SEASON,
        FootballCalendarEvent.to_football_calendar_events(fixtures)
    )
    with open(f'{OUTPUT_PATH}/calendar.ics', 'wb') as f:
        f.write(cal.to_bytes())


if __name__ == '__main__':
    main()
    # asyncio.run(fetch_data())
