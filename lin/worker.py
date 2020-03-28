# -*- coding: utf-8 -*-

import logging

import asyncio

from lin.http.parser import HTTP_v1_x_Parser as HTTParser
from lin.http.handlers.wsgihandler import WSGIHandler
from lin.http.excepts import ( 
        NoMoreData, LimitRequestLine, LimitRequestHeader,
        InvalidRequestMethod, LimitRequestLine, LimitRequestLine
        )

logger = logging.getLogger(__name__)

class Worker:
    def __init__(self, conf):
        self.conf = conf
        self.parser_cls = HTTParser
        self.handler = conf.handler
        #self.semaphore = asyncio.Semaphore(conf.connections)

    def except_handle(self, addr, e):
        if isinstance(e, NoMoreData):
            logger.debug('Ignored client: {}:{} early disconnection'.format(*addr)) 
        elif isinstance(e, BrokenPipeError):
            logger.debug('Ignored client: {}:{} broken pipe'.format(*addr))
        elif isinstance(e, ConnectionResetError):
            logger.debug('Ignored client: {}:{} connection reset by peer'.format(*addr))
        elif isinstance(e, asyncio.TimeoutError):
            logger.debug('Ignored client: {}:{} keepalive timeout'.format(*addr))
        elif isinstance(e, (LimitRequestLine, LimitRequestHeader, InvalidRequestMethod, LimitRequestLine, LimitRequestLine)):
            logger.debug('Parsing exception {}'.format(str(e)))
        else:
            logger.warning('Unknown exception: {} from {}:{}'.format(str(e), *addr))
            logger.exception(e)

    async def process(self, client, addr):
        #async with self.semaphore:
        parser = self.parser_cls(client, addr, self.conf)
        while True:
            try:
                req, resp = await parser.parse()
                self.handler.handle(req, resp)
                await resp.flush()
            except Exception as e:
                self.except_handle(addr, e)
                break

            if resp.should_close:
                break

        client.close()
