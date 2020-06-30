# -*- coding: utf-8 -*-

import re

from urllib.parse import unquote

from lin.http.handlers.ihandler import IHandler

class IRule:
    def replace(self, request):
        raise NotImplementedError()

class RegexPatternRule(IRule):
    def __init__(self, pattern, replacement):
        self.pattern = pattern
        self.replacement = replacement
        self.regex = re.compile(self.pattern)

    def replace(self, request):
        uri = unquote(request.uri, 'latin1')
        match = self.regex.match(uri)
        if match:
            groups = match.groups()
            request.uri = self.replacement.format(*groups)
            return True
        return False

class RewriteHandler(IHandler):
    def __init__(self, rules):
        self.rules = rules 

    def add_rule(self, rule):
        self.rules.append(rule)

    def handle(self, request, response):
        for rule in self.rules:
            if rule.replace(request):
                break
