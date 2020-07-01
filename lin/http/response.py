# -*- coding: utf-8 -*-

import os
import collections

from lin.utils import bytes_to_str, str_to_bytes, http_date
from lin.http.header import Header

class IWriter:

    def tell(self):
        return -1

    def fileno(self):
        raise NotImplementedError()

    def write(self, data):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class Writer(IWriter):
    def __init__(self, write):
        self._write = write
        self._raw = None

    def write(self, data):
        self._write(data)

    def __iter__(self):
        yield from self._raw

    def tell(self):
        if hasattr(self._raw, 'fileno') and hasattr(self._raw, 'tell'):
            return self._raw.tell()
        else:
            return super().tell()

    def fileno(self):
        if hasattr(self._raw, 'fileno'):
            return self._raw.fileno()
        else:
            return super().fileno()

    def close(self):
        if hasattr(self._raw, 'fileno'):
            self._raw.close()

    def __call__(self, raw):
        if not self._raw is None:
            raise AssertionError("body has been initialized")
        if not (isinstance(raw, collections.Iterable) or hasattr(raw, 'fileno')):
            raise TypeError("'raw' object is not iterable or file")
        self._raw = raw

class Response:
    def __init__(self, version, header, should_close, writer, sendfile):
        self.version = version
        self._header = header
        self._body = None
        self._status = None
        self.writer = writer
        self.should_close = should_close
        self.header_sent = False
        self.sendfile = sendfile

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, header):
        if not isinstance(header, Header): 
            raise TypeError('{} must be an Header'.format(header))
        self._header = header

    def __enter__(self):
        self._body = Writer(self.blocking_write)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._body = None

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, writer):
        if not isinstance(writer, IWriter): 
            raise TypeError('{} must be an IWriter'.format(writer))
        self._body = writer

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status
        status_code, status_text = self.status.split(None, 1)
        self.status_code = int(status_code)

    @property
    def chunked(self):
        if self.header.get('Transfer-Encoding') == 'chunked':
            return True
        if self.header.get('Content-Length') is not None:
            return False
        elif self.version <= 'HTTP/1.0':
            return False
        return False

    def header_to_bytes(self):
        if self.status is None:
            raise AssertionError("response status not set")

        status_line = "{} {}\r\n".format(self.version, self.status)
        self.header.set('Date', http_date())
        self.header.set('Connection', 'close' if self.should_close or self.status_code != 200 else 'keep-alive')
        header_bytes = self.header.to_bytes()
        return str_to_bytes(status_line) + header_bytes

    def blocking_write(self, data):
        self.blocking_send_header()
        if self.is_chunked():
            data = self.to_chunk(data)
        self.writer.blocking_write(data)

    def blocking_send_header(self):
        if not self.header_sent:
            self.writer.blocking_write(self.header_to_bytes())
            self.header_sent = True

    @classmethod
    def to_chunk(cls, data):
        size = b"%X\r\n" % len(data)
        return b''.join([size + data + b'\r\n'])

    async def send_header(self):
        if not self.header_sent:
            await self.writer.sendall(self.header_to_bytes())
            self.header_sent = True

    async def _send_file(self, fd, offset, nbytes, chunked=False):
        if chunked:
            await self.writer.sendall(b"%X\r\n" % nbytes)

        await self.writer.sendfile(fd, offset, nbytes)

        if chunked:
            await self.writer.sendall(b"\r\n")

    async def _send_data(self, data, chunked=False):
        if chunked:
            await self.writer.sendall(self.to_chunk(data))
        else:
            await self.writer.sendall(data)

    async def flush(self):
        await self.send_header()

        if self.sendfile and self.body.tell() >= 0:
            content_length = int(self.header.get('Content-Length'))
            offset = self.body.tell()
            filesize = os.fstat(self.body.fileno()).st_size

            if filesize == 0:
                self.body.close()
                return

            count = content_length if content_length else filesize - offset
            await self._send_file(self.body, offset, count, self.chunked)
        else:
            for part in self.body:
                await self._send_data(part, self.chunked)

        if self.chunked:
            await self._send_data(b'', self.chunked)

        self.body.close()
