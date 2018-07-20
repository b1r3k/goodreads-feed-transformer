import asyncio
import logging

from aiohttp import web

logger = logging.getLogger(__name__)


def initialize_endpoints(app, settings):
    logger.info('Initializing http endpoints')
    app.router.add_get('/user_status/list/:user', get_user_status_list)


async def get_user_status_list(req):
    req.match = ''
    return web.Response(text="Welcome home!")


def app(global_config, **settings):
    config_filename = global_config.get('__file__')
    logging.config.fileConfig(config_filename or {}, global_config, False)
    debug = settings.get('debug') == 'True'

    loop = asyncio.get_event_loop()
    loop.set_debug(debug)

    app = web.Application(logger=logger, loop=loop)

    initialize_endpoints(app, settings)

    return app
