from asynctest import CoroutineMock, MagicMock
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

import transformer
from transformer import const


class HttpRouting(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app[const.DB_REDIS] = redis_mock = MagicMock()
        redis_mock.setnx = CoroutineMock()
        redis_mock.setex = CoroutineMock()
        app[const.SETTINGS] = {}
        app[const.HTTP_SESSION] = CoroutineMock()
        transformer.main.initialize_endpoints(app)
        return app

    @unittest_run_loop
    async def test_location_first_enter(self):
        data = {
            "occurredAt": "October 19, 2016 at 07:05PM",
            "locationMapUrl": "{{LocationMapUrl}}",
            "action": "entered",
            "secret": "YmUwNWY5MWRmMWJjOWRlNWFlZTJmNzdk"
        }
        resp = await self.client.request("POST", "/location/device_id/location_id/event_name", json=data)
        assert resp.status == 200
        self.app[const.DB_REDIS].setnx.assert_awaited()
        self.app[const.DB_REDIS].setex.assert_awaited()
