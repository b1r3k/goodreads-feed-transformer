import logging
import hmac
import json

from aiohttp import web

from .const import SETTINGS, HTTP_SESSION, GH_SECRET


logger = logging.getLogger(__name__)


async def handle_github_webhook(req):
    settings = req.app[SETTINGS]
    session = req.app[HTTP_SESSION]
    github_event = req.headers.get('X-GitHub-Event')
    logger.info(req.headers)
    try:
        github_user = req.match_info['user']
    except Exception:
        raise web.HTTPBadRequest(reason='unknown event=%s/user=%s' % (github_event, req.match_info))
    try:
        logger.info('Received github webhook for event %s, user: %s', github_event, github_user)
        hash_alg, body_signature = req.headers.get('X-Hub-Signature').split('=')
        body = await req.read()
        expected_signature = hmac.new(settings[GH_SECRET].encode(), msg=body, digestmod=hash_alg).hexdigest()
        if not body_signature == expected_signature:
            msg = 'Invalid {} signature, got {} but expected: {}'.format(hash_alg, body_signature, expected_signature)
            logger.debug(msg)
            raise web.HTTPForbidden(reason=msg)
    except (KeyError,):
        raise web.HTTPForbidden(reason='invalid body signature')
    # accepted events
    if github_event not in ['push']:
        logger.debug('Unexpected event arrived, skipping..')
        return web.HTTPOk()
    payload = json.loads(body)

    return web.HTTPOk()
