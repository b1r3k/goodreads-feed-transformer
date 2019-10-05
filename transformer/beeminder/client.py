import logging
from urllib.parse import urljoin

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError, ClientResponseError

logger = logging.getLogger(__name__)


class BeeminderClient:
    BASE_URL = 'https://www.beeminder.com/api/v1/'

    def __init__(self, username, auth_token, session=None, session_factory=ClientSession):
        self._username = username
        self._auth_token = auth_token
        self._session = session
        self._session_factory = session_factory

    async def _make_request(self, *args, **kwargs):
        if self._session is None:
            self._session = self._session_factory()
        query_params = kwargs.get('params', {})
        query_params = {param: value for param, value in query_params.items() if value is not None}
        query_params.update(dict(auth_token=self._auth_token))
        kwargs.update(dict(params=query_params))
        logger.info('Query params: %s', kwargs['params'])
        async with self._session.request(*args, **kwargs) as resp:
            payload = await resp.json()
            try:
                resp.raise_for_status()
                return payload
            except ClientResponseError as ex:
                reason = payload.get('errors') or getattr(ex, 'reason')
                updated_resp_error = ClientResponseError(ex.request_info,
                                                         ex.history,
                                                         status=ex.status,
                                                         message=reason,
                                                         headers=ex.headers)
                raise updated_resp_error

    def _get_endpoint_url(self, url):
        return urljoin(self.BASE_URL, url)

    async def get_user(self, username='me', associations: bool = False, diff_since: int = None, skinny: bool = False,
                       datapoints_count: int = None):
        params = dict(
            associations='true' if associations else 'false',
            skinny='true' if skinny else 'false',
        )
        if diff_since:
            params.update(dict(diff_since=diff_since))
        if datapoints_count:
            params.update(dict(datapoints_count=datapoints_count))

        url = self._get_endpoint_url('users/{}.json'.format(username))
        return await self._make_request('GET', url, params=params)

    async def get_goal(self, goal_name, username: str = None, datapoints: bool = False):
        username = username if username else self._username
        params = dict(
            datapoints=datapoints
        )
        url = self._get_endpoint_url('users/{username}/goals/{goal_name}'.format(username=username,
                                                                                 goal_name=goal_name))
        return await self._make_request('GET', url, params=params)

    async def get_all_goals(self, username: str = None):
        username = username if username else self._username
        url = 'users/{username}/goals.json'.format(username=username)
        return await self._make_request('GET', url)

    async def get_all_datapoints(self, goal_name, username: str = None, sort: str = 'id'):
        username = username if username else self._username
        params = dict(
            sort=sort
        )
        url = self._get_endpoint_url('users/{user}/goals/{goal}/datapoints.json'.format(user=username, goal=goal_name))
        return await self._make_request('GET', url, params=params)

    async def create_datapoint(self, goal_name, value, username: str = None, timestamp: int = None,
                               daystamp: str = None, comment: str = None, requestid: str = None):
        username = username if username else self._username
        params = dict(
            value=value,
            timestamp=timestamp,
            daystamp=daystamp,
            comment=comment,
            requestid=requestid
        )
        url = self._get_endpoint_url('users/{user}/goals/{goal}/datapoints.json'.format(user=username,
                                                                                        goal=goal_name))
        return await self._make_request('POST', url, params=params)

    async def update_datapoint(self, goal_name, datapoint_id, value, username: str = None, timestamp: int = None,
                               comment: str = None):
        username = username if username else self._username
        url = self._get_endpoint_url('users/{u}/goals/{g}/datapoints/{id}.json'.format(u=username, g=goal_name,
                                                                                       id=datapoint_id))
        params = dict(
            value=value,
            timestamp=timestamp,
            comment=comment
        )
        return await self._make_request('PUT', url, params=params)

    async def delete_datapoint(self, goal_name, datapoint_id, username: str = None):
        username = username if username else self._username
        url = self._get_endpoint_url('users/{u}/goals/{g}/datapoints/{id}.json'.format(u=username, g=goal_name,
                                                                                       id=datapoint_id))
        return await self._make_request('DELETE', url)
