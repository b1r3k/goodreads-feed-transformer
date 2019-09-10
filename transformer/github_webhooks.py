import logging
import hmac

from aiohttp import web

from .const import *


logger = logging.getLogger(__name__)


async def handle_github_webhook(req):
    settings = req.app[SETTINGS]
    session = req.app[HTTP_SESSION]
    try:
        github_user = req.match_info['user']
        github_event = req.headers.get('X-GitHub-Event').split('=')[1]
    except Exception:
        raise web.HTTPBadRequest(reason='unknown event/user')
    try:
        body_signature = req.headers.get('X-Hub-Signature')
        logger.info('Received github webhook for event %s, user: %s', github_event, github_user)
        body = await req.read()
        expected_signature = hmac.new(settings.get(GH_SECRET), body).hexdigest()
        assert body_signature == expected_signature
    except Exception:
        raise web.HTTPForbidden(reason='invalid body signature')
