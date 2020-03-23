# -*- coding: utf-8 -*-

class NoMoreData(IOError):
    def __str__(self):
        return "No more data"

class OverflowException(Exception):
    def __init__(self, limit):
        self.limit = limit

    def __str__(self):
        return "Overflow limit size (%d)" % self.limit

class LimitRequestLine(Exception):
    def __init__(self, size):
        self.size = size

    def __str__(self):
        return "Request Line is too large (%d)" % self.size

class LimitRequestHeader(Exception):
    def __init__(self, size):
        self.size = size

    def __str__(self):
        return "Request Header is too large (%d)" % self.size

class InvalidHeader(Exception):
    def __init__(self, header):
        self.header = header

    def __str__(self):
        return "Invalid HTTP Header: %s" % self.header 

class InvalidRequestMethod(Exception):
    def __init__(self, method):
        self.method = method

    def __str__(self):
        return "Invalid HTTP method: %s" % self.method

class InvalidChunk(Exception):
    def __init__(self, chunk):
        self.chunk = chunk

    def __str__(self):
        return "Invalid chunk (%s)" % self.chunk
