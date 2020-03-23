# -*- coding: utf-8 -*-

from lin.http.handlers.ihandler import IHandler

class ChainHandler(IHandler):
    def __init__(self, handlers):
        self.handlers = handlers

    def handle(self, request, response):
        for handler in self.handlers:
            interrupt = handler.handle(request, response)
            if not interrupt is None:
                return interrupt

    def add_handler(self, handler):
        self.handlers.append(handler)
