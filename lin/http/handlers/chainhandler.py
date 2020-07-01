# -*- coding: utf-8 -*-

from lin.http.handlers.ihandler import IHandler

class ChainHandler(IHandler):
    def __init__(self, handlers):
        self.handlers = handlers

    def add_handler(self, handler):
        self.handlers.append(handler)

    async def handle(self, request, response):
        for handler in self.handlers:
            interrupt = await handler.handle(request, response)
            if not interrupt is None:
                return interrupt

