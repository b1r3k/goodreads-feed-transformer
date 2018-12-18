import asyncio
import logging
import re
import time
import signal
from email.utils import parsedate_to_datetime

import lxml.html
import lxml.etree


from aiohttp import web, ClientSession
import aioredis

from .const import *
from .store.events import store_event_marker, remove_event_marker, get_event_marker

logger = logging.getLogger(__name__)


class ParserError(BaseException):
    pass


async def trigger_maker_event(http_session, event_name, data, maker_key):
    url = 'https://maker.ifttt.com/trigger/{}/with/key/{}'.format(event_name, maker_key)
    async with http_session as http:
        await http.post(url, json=data)


async def handle_location(req):
    dbredis = req.app[DB_REDIS]
    settings = req.app[SETTINGS]
    session = req.app[HTTP_SESSION]
    device_id = req.match_info['device_id']
    location_id = req.match_info['location_id']
    event_name = req.match_info['event_name']
    event_marker_id = '{}/{}/{}'.format(device_id, location_id, event_name)
    data = await req.json()
    if data['secret'] != IFTTT_APPLET_SECRET:
        raise web.HTTPForbidden(reason='bad secret')
    try:
        if data['action'].lower() == 'entered':
            occured_at = data.get('occuredAt', None)
            if occured_at:
                occured_at = parsedate_to_datetime(occured_at)
                occured_at = occured_at.timestamp()
            await store_event_marker(dbredis, event_marker_id, occured_at)
        if data['action'].lower() == 'exited':
            started_at = await get_event_marker(dbredis, event_marker_id)
            if started_at is None:
                logger.error('Got exit but never entered for location: %s from device: %s', location_id, device_id)
            now = int(time.time())
            delta = now - int(started_at) / 60. / 60.  # seconds -> hours
            payload = {
                'value1': float("{0:.2f}".format(delta))
            }
            await trigger_maker_event(session, event_name, payload, settings['ifttt.maker_key'])
            await remove_event_marker(dbredis, event_marker_id)
        return web.HTTPOk()
    except Exception:
        logger.exception('Cannot handle data: %s', data)
        raise web.HTTPServerError()


def initialize_endpoints(app):
    logger.info('Initializing http endpoints')
    app.router.add_get('/user_status/list/{user_id}', get_user_status_list)
    app.router.add_post('/location/{device_id}/{location_id}/{event_name}', handle_location)


def get_data(title_str):
    """
    Lukasz is on page 80 of 496 of The Moral Animal
    OR
    Lukasz is 67% done with The Brothers Karamazov

    :param title_str:
    :return: 80, 496
    """
    pages_regex = re.compile('.*\s(\d+)\sof\s(\d+)\sof\s(.*)')
    try:
        match = pages_regex.match(title_str)
        read = int(match.group(1))
        total = int(match.group(2))
        book_title = match.group(3)
    except AttributeError:
        raise ParserError('Cannot parse string: %s' % title_str)
    return read, total, book_title


def transform_feed(feed_text):
    feed_items = {}
    parser = lxml.etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
    feed = lxml.etree.fromstring(feed_text, parser)
    items = feed.xpath('//rss/channel/item')
    for item in items:
        title = item.xpath('title')[0]
        date_raw = item.xpath('pubDate')[0]
        date = parsedate_to_datetime(date_raw.text)
        try:
            current_page, total, book_title = get_data(title.text)
        except ParserError:
            logger.warning('Cannot parse string: %s', title.text)
            continue
        updates = feed_items.get(book_title, [])
        updates.append((current_page, total, date))
        feed_items[book_title] = updates
    for item in items:
        title = item.xpath('title')[0]
        date_raw = item.xpath('pubDate')[0]
        date = parsedate_to_datetime(date_raw.text)
        diff = None
        try:
            current_page, total, book_title = get_data(title.text)
        except ParserError:
            logger.warning('Cannot parse string: %s', title.text)
            continue
        for update in sorted(feed_items[book_title], key=lambda k: k[2], reverse=True):
            if date > update[2]:
                diff = current_page - update[0]
                break
        # no updates before? means it's first update
        if diff is None:
            diff = current_page
        desc_tag = item.xpath('description')[0]
        desc_tag.text = str(diff)
    xml_as_str = lxml.etree.tostring(feed, encoding='utf8', pretty_print=True)
    return xml_as_str


async def get_user_status_list(req):
    user_id =req.match_info['user_id']
    if not user_id:
        return web.HTTPBadRequest(text='Expected /user_status/list/{user_id}')
    goodreads_url = 'https://www.goodreads.com/user_status/list/{}?format=rss'.format(user_id)
    async with ClientSession() as session:
        headers = {}
        try:
            logger.info('Checking cache..')
            with open('./data/{}'.format(user_id), 'r') as cache:
                data = cache.readline()
                lastmodm, last_etag = data.strip().split(' ')
            headers['If-Modified-Since'] = lastmodm
            headers['If-None-Match'] = last_etag
        except FileNotFoundError:
            pass
        async with session.get(goodreads_url, headers=headers) as resp:
            logger.info('')
            if resp.status == 304:
                return web.HTTPNotModified()
            last_modified = resp.headers.get('last-modified', '')
            etag = resp.headers.get('etag', '')
            if last_modified and etag:
                with open('./data/{}'.format(user_id), 'w') as cache:
                    cache.write('{} {}'.format(last_modified, etag))
            raw_feed = await resp.text()
            new_feed = transform_feed(raw_feed.encode('utf-8'))
    return web.Response(body=new_feed, content_type='application/rss+xml')


async def bootstrap(app):
    settings = app[SETTINGS]
    redis_addr = settings.get('db.redis', 'localhost:6379')
    host, port = redis_addr.strip().split(':')
    app[DB_REDIS] = await asyncio.wait_for(
        aioredis.create_redis_pool((host, int(port)), minsize=0, maxsize=5, loop=app.loop), 3, loop=app.loop)
    app[HTTP_SESSION] = ClientSession()


async def stop_all():
    await app[HTTP_SESSION].close()
    app[DB_REDIS].close()
    await app[DB_REDIS].wait_closed()


def app(global_config, **settings):
    config_filename = global_config.get('__file__')
    logging.config.fileConfig(config_filename or {}, global_config, False)
    debug = settings.get('debug') == 'True'

    loop = asyncio.get_event_loop()
    loop.set_debug(debug)

    app = web.Application(logger=logger, loop=loop)
    app[SETTINGS] = settings

    app.on_startup.append(bootstrap)
    app.on_cleanup.append(stop_all)
    signal.signal(signal.SIGINT, app.shutdown)
    signal.signal(signal.SIGTERM, app.shutdown)
    initialize_endpoints(app)
    app.freeze()

    return app
