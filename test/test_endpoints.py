from pathlib import Path
from io import BytesIO
from http.server import BaseHTTPRequestHandler

from asynctest import CoroutineMock, MagicMock
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

import transformer
from transformer import const


def read_fixture(path, decoder=None):
    fixture_path = Path('test', 'fixtures', path)

    with open(fixture_path.resolve(), 'rb') as fd:
        content = fd.read()
        if decoder:
            return decoder(content)
        else:
            return str(content, 'utf-8')


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()
        # BaseHTTPRequestHandler.parse_request encodes string with iso-8859-1
        self.path = str(bytes(self.path, 'iso-8859-1'), 'utf-8')

    def send_error(self, code, message=None, explain=None):
        raise ValueError("code %d, message %s" % (code, message))


class HttpRouting(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app[const.DB_REDIS] = redis_mock = MagicMock()
        redis_mock.setnx = CoroutineMock()
        redis_mock.setex = CoroutineMock()
        app[const.SETTINGS] = {
            const.GH_SECRET: 'GH_SECRET'
        }
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

    @unittest_run_loop
    async def test_github_webhook(self):
        req = read_fixture('github_ping.req', decoder=HTTPRequest)
        body = req.rfile.read()
        resp = await self.client.request("POST", "/github/b1r3k", data=body, headers=req.headers)
        assert resp.status == 200
        return
