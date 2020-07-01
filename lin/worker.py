# -*- coding: utf-8 -*-

import logging
import socket
import asyncio

from lin.utils import str_to_bytes
from lin.version import __SERVER_NAME__

from lin.http.header import Header
from lin.http.response import Response

from lin.http.parser import HTTP_v1_x_Parser as HTTParser
from lin.http.handlers.wsgihandler import WSGIHandler
from lin.http.excepts import ( 
        NoMoreData, LimitRequestLine, LimitRequestHeader,
        InvalidRequestMethod, InvalidHeader
        )

logger = logging.getLogger(__name__)

class Worker:
    def __init__(self, conf):
        self.conf = conf
        self.parser_cls = HTTParser
        self.handler = conf.handler

    async def handle_except(self, writer, status_code, reason):
        TEMPLATE = '''<html>
            <head><title>{0} {1}</title></head>
            <body bgcolor="white">
                <center><h1>{0} {1}</h1></center>
            </body>
        </html>
        '''
        content = str_to_bytes(TEMPLATE.format(status_code, reason))
        header = Header()
        header.set('Server', __SERVER_NAME__)
        header.set('Content-Type', 'text/html')
        header.set('Content-Length', len(content))

        resp = Response('HTTP/1.1', header, True, writer, False)
        resp.status = '{} {}'.format(status_code, reason)
        with resp:
            resp.body([content])
            await resp.flush()

    async def process(self, client):
        parser = self.parser_cls(client, self.conf)
        while True:
            try:
                req, resp = await parser.parse()
                with req, resp:
                    await self.handler.handle(req, resp)
                    await resp.flush()
            except NoMoreData as e:
                logger.debug('Ignore client disconnect early')
                break
            except socket.error as e:
                logger.debug('Socket exception: {}'.format(e))
                break
            except asyncio.TimeoutError as e:
                logger.debug('Ignore client connection timeout')
                break
            except (LimitRequestLine, LimitRequestHeader, InvalidHeader, InvalidRequestMethod) as e:
                logger.warning('Parsing exception {}'.format(e))
                await self.handle_except(client, 400, 'Bad Request')
                break
            except Exception as e:
                logger.warning('Unknown exception: {}'.format(e))
                logger.exception(e)
                await self.handle_except(client, 500, 'Internal Server Error')
                break
            if resp.should_close:
                break

        client.close()
