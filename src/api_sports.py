import json
import logging
import os


class APISports:
    API_HOST = 'v3.football.api-sports.io'
    BASE_URL = f'https://{API_HOST}'
    HEADERS = {
        'x-rapidapi-host': API_HOST,
        'x-rapidapi-key': os.getenv('API_SPORTS_API_KEY')
    }

    def __init__(self):
        assert self.HEADERS['x-rapidapi-key']

    async def get_fixtures(self, client, team, season):
        url = f'{self.BASE_URL}/fixtures?team={team}&season={season}'
        return await self._make_non_paging_request(client, url)

    async def _make_non_paging_request(self, client, url):
        async with client.get(url, headers=self.HEADERS) as r:
            logging.info(f'About to make non-paging request: url={url}')
            if r.status < 200 or r.status > 299:
                logging.info(f'Received NON 200 response: status code={r.status}, url={url}')
                return []
            rj = await r.json()
            if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                logging.debug(
                    f'Received response: url={url}, status code={r.status}, response headers={r.headers}, response payload=')
                logging.debug(json.dumps(rj, indent=2))
            if rj['paging']['total'] > 1:
                raise Exception('Unexpected response from a non paging request (make a paging request instead?)')
            response = rj['response']
            return response
