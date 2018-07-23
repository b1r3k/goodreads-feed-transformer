import asyncio
import logging
import re
from email.utils import parsedate_to_datetime

import lxml.html
import lxml.etree


from aiohttp import web, ClientSession


logger = logging.getLogger(__name__)


class ParserError(BaseException):
    pass


def initialize_endpoints(app, settings):
    logger.info('Initializing http endpoints')
    app.router.add_get('/user_status/list/{user_id}', get_user_status_list)


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
            read, total, book_title = get_data(title.text)
        except ParserError:
            logger.warning('Cannot parse string: %s', title.text)
            continue
        updates = feed_items.get(book_title, [])
        updates.append((read, total, date))
        feed_items[book_title] = updates
    for item in items:
        title = item.xpath('title')[0]
        date_raw = item.xpath('pubDate')[0]
        date = parsedate_to_datetime(date_raw.text)
        try:
            read, total, book_title = get_data(title.text)
        except ParserError:
            logger.warning('Cannot parse string: %s', title.text)
            continue
        for update in sorted(feed_items[book_title], key=lambda k: k[2], reverse=True):
            if date > update[2]:
                diff = read - update[0]
                content_tag = lxml.etree.SubElement(item, 'content')
                content_tag.text = str(diff)
                break
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
            with open('./data/{}'.format(user_id), 'r') as cache:
                data = cache.readline()
                lastmodm, last_etag = data.strip().split(' ')
            headers['If-Modified-Since'] = lastmodm
            headers['If-None-Match'] = last_etag
        except FileNotFoundError:
            pass
        async with session.get(goodreads_url, headers=headers) as resp:
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


def app(global_config, **settings):
    config_filename = global_config.get('__file__')
    logging.config.fileConfig(config_filename or {}, global_config, False)
    debug = settings.get('debug') == 'True'

    loop = asyncio.get_event_loop()
    loop.set_debug(debug)

    app = web.Application(logger=logger, loop=loop)

    initialize_endpoints(app, settings)

    return app
