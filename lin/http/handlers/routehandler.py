# -*- coding: utf-8 -*-

import re

from urllib.parse import unquote

from lin.http.handlers.ihandler import IHandler

class IRule:
    def match(self, request):
        raise NotImplementedError()

class UriRule(IRule):
    def __init__(self, pattern, handler):
        self.pattern = pattern
        self.handler = handler
        self.regex = re.compile(self.pattern)

    def match(self, request):
        uri = unquote(request.uri, 'latin1')
        return self.regex.match(uri)

class RouteHandler(IHandler):
    def __init__(self, rules):
        self.rules = rules

    def add_rule(self, rule):
        self.rules.append(rule)

    async def handle(self, request, response):
        for rule in self.rules:
            if rule.match(request):
                return await rule.handler.handle(request, response)
