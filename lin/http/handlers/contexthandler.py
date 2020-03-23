# -*- coding: utf-8 -*-

from lin.http.handlers.ihandler import IHandler

class ContextHandler(IHandler):
    def __init__(self, rules):
        self.rules = rules

    def handle(self, request, response):
        pass

