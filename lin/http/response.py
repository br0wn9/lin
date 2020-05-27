# -*- coding: utf-8 -*-

import os
import collections

from lin.utils import bytes_to_str, str_to_bytes, http_date
from lin.http.header import Header

class IWriter:
    def open(self):
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
        self._file = None
        self._content = None

    def open(self):
        return self._file

    def write(self, data):
        self._write(data)

    def __iter__(self):
        yield from self._content

    def close(self):
        if self._file:
            self._file.close()

    def set_file(self, file):
        if not hasattr(file, 'fileno'):
            raise TypeError("'file' object is not file")
        self._file = file

    def set_content(self, content):
        if not isinstance(content, collections.Iterable):
            raise TypeError("'content' object is not iterable")
        self._content = content

class Response:
    def __init__(self, version, header, should_close, writer, sendfile):
        self.version = version
        self._header = header
        self._body = None
        self.writer = writer
        self.status = None
        self.should_close = should_close
        self.header_sent = False
        self._sendfile = sendfile

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, header):
        if not isinstance(header, Header): 
            raise TypeError('{} must be an Header'.format(header))
        self._header = header

    def __enter__(self):
        self._body = Writer(self.write)
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

    def set_status(self, status):
        self.status = status
        status_code, _ = self.status.split(None, 1)
        self.status_code = int(status_code)

    def is_chunked(self):
        if self.header.get('Transfer-Encoding') == 'chunked':
            return True
        if self.header.get('Content-Length') is not None:
            return False
        elif self.version <= '1.0':
            return False
        return False

    def chunk_wrap(self, data):
        chunk_size = b"%X\r\n" % len(data)
        return b''.join([chunk_size + data + b'\r\n'])

    def header_dump(self):
        if self.status is None:
            raise AssertionError("Response header not set")

        status_line = "HTTP/{} {}\r\n".format(self.version, self.status)
        self.header.set('Date', http_date())
        self.header.set('Connection', 'close' if self.should_close else 'keep-alive')
        header_str = self.header.dump()
        return status_line + header_str

    def write(self, data):
        if not self.header_sent:
            self.writer.blocking_write(str_to_bytes(self.header_dump()))
            self.header_sent = True
        if self.is_chunked():
            data = self.chunk_wrap(data)
        self.writer.blocking_write(data)

    async def send_header(self):
        if not self.header_sent:
            await self.writer.sendall(str_to_bytes(self.header_dump()))
            self.header_sent = True

    async def flush(self):
        await self.send_header()

        file = self.body.open()
        if self._sendfile and not file is None:
            content_length = self.header.get('Content-Length')
            offset = file.tell()
            size = os.fstat(file.fileno()).st_size
            count = int(content_length) if content_length else size - offset

            if self.is_chunked():
                await self.writer.sendall(b"%X\r\n" % count)

            await self.writer.sendfile(file, offset, count)

            if self.is_chunked():
                await self.writer.sendall(b"\r\n")
        else:
            for part in self.body:
                if self.is_chunked():
                    await self.writer.sendall(self.chunk_wrap(part))
                else:
                    await self.writer.sendall(part)

        if self.is_chunked():
            await self.writer.sendall(self.chunk_wrap(b''))

        self.body.close()
