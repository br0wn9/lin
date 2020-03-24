# -*- coding: utf-8 -*-

from io import BytesIO

from lin.utils import bytes_to_str, str_to_bytes, http_date

from lin.version import __SERVER_NAME__
from lin.http.header import Header
from lin.http.request import Request
from lin.http.response import Response
from lin.http.excepts import NoMoreData, LimitRequestLine, InvalidRequestMethod, OverflowException


class Reader:
    def __init__(self, sock, buffer_size):
        self.sock = sock
        self.buff = BytesIO()
        self.buffer_size = buffer_size

    def read_line(self):
        while True:
            data = self.buff.getvalue()
            idx = data.find(b'\r\n')
            if idx >= 0:
                self.buff = BytesIO()
                self.buff.write(data[idx + 2:])
                return data[:idx + 2]
            part = self.sock.blocking_read(5)
            self.buff.write(part)

    def read(self, size, timeout = None):
        pre_size = len(self.buff.getvalue())
        if pre_size >= size > 0:
            data = self.buff.getvalue()
            self.buff = BytesIO()
            self.buff.write(data[size:])
            return data[:size]
        else:
            part = self.sock.blocking_read(size - pre_size, timeout)
            if pre_size == 0:
                return part
            else:
                self.buff.write(part)
                data = self.buff.getvalue()
                self.buff = BytesIO()
                return data

    async def preread(self):
        await self.read_part()

    async def read_part(self):
        data = await self.sock.recv(self.buffer_size)
        if not data:
            raise NoMoreData()
        self.buff.write(data)

    async def find(self, substr, limit):
        while True:
            data = self.buff.getvalue()
            idx = data.find(substr)
            if idx >= 0:
                if idx > limit > 0:
                    raise OverflowException(limit)
                break
            elif len(data) > limit > 0:
                raise OverflowException(limit)
            await self.read_part()
        self.buff = BytesIO()
        self.buff.write(data[idx + len(substr):])
        return data[:idx]
        
class HTTP_v1_x_Parser:

    VERSIONS = ('1.0', '1.1')
    METHODS = ('GET', 'POST', 'HEAD', 'OPTIONS', 'PUT', 'PATCH', 'DELETE', 'TRACE', 'CONNECT')

    def __init__(self, sock, addr, cfg):
        self.sock = sock
        self.addr = addr
        self.cfg = cfg
        self.reader = Reader(sock, cfg.buffer_size)

    async def parse_headers(self):
        headers = []
        header_lines = await self.read_headers()
        for field in header_lines.split('\r\n'):
            parts = field.split(':', 1)
            if len(parts) != 2:
                raise InvalidHeader(field.strip())
            name, value = parts[0].strip(), parts[1].strip()
            headers.append((name, value))
        return headers
        
    async def parse_request_line(self):
        request_line = await self.read_request_line()
        parts = request_line.split(None, 2)

        if len(parts) != 3:
            raise InvalidRequestLine(request_line)

        method = parts[0].upper()
        if method not in self.METHODS:
            raise InvalidRequestMethod(method)

        ver_parts = parts[2].split('/', 1)
        if len(ver_parts) != 2 or ver_parts[0].upper() != 'HTTP' or ver_parts[1] not in self.VERSIONS:
            raise InvalidHTTPVersion(part[2])

        return method, parts[1], ver_parts[1]

    async def read_request_line(self):
        try:
            request_line_b = await self.reader.find(b'\r\n', self.cfg.limit_request_line)
            return bytes_to_str(request_line_b)
        except OverflowException:
            raise LimitRequestLine(self.cfg.limit_request_line)

    async def read_headers(self):
        try:
            headers_b = await self.reader.find(b'\r\n\r\n', self.cfg.limit_request_header)
            return bytes_to_str(headers_b)
        except OverflowException:
            raise LimitRequestHeader(self.cfg.limit_request_header)

    async def parse(self):
        await self.reader.preread()

        method, uri, version = await self.parse_request_line()

        fields = await self.parse_headers()
        header = Header(fields)

        req = Request(method, uri, version, header, self.sock.getsockname(), self.reader)

        expect = req.header.get('expect') 
        if expect and expect == '100-continue':
            await self.sock.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")

        req.init_body()
        
        header = Header()
        header.set('Server', __SERVER_NAME__)
        resp = Response(version, header, req.should_close(), self.sock)
        return req, resp 
