# -*- coding: utf-8 -*-

import sys
import time

from io import BytesIO

from lin.http.excepts import InvalidChunk, InvalidHeader
from lin.http.header import Header


class IReader:
    def read(self, size):
        raise NotImplementedError()

class ChunkReader(IReader):
    def __init__(self, reader):
        self.reader = reader
        self.remain_size = None

    def read_chunk(self):
        chunk_size = self.read_chunk_size()

        data = self.reader.read(chunk_size + 2)
        return data[:-2]
        
    def read_chunk_size(self):
        size = self.reader.read_line()
        try:
            return int(size[:-2], 16)
        except ValueError:
            raise InvalidChunk(size)

    def read_remain_chunk(self):
        data = self.reader.read(self.remain_size + 2)
        return data[:-2]
        
    def read(self, size):
        if size == 0 or self.remain_size == 0:
            return b''

        # initialize the chunk size
        if self.remain_size is None:
            self.remain_size = self.read_chunk_size()
            if self.remain_size == 0:
                self.read_remain_chunk()
                return b''

        buff = BytesIO()

        while True:
            pre_size = len(buff.getvalue())
            known_size = pre_size + self.remain_size

            if size >= known_size:
                data = self.read_remain_chunk()
                buff.write(data)
                self.remain_size = self.read_chunk_size()

                if self.remain_size == 0:
                    self.read_remain_chunk()
                    return buff.getvalue()
                elif size == known_size:
                    return buff.getvalue()
                else:
                    continue
            else:
                data = self.reader.read(size - pre_size)
                buff.write(data)
                self.remain_size = known_size - size
                return buff.getvalue()


class LengthReader(IReader):
    def __init__(self, reader, length):
        self.length = length
        self.reader = reader

    def read(self, size):
        length = min(self.length, size)
        if length == 0:
            return b''
        else:
            data = self.reader.read(length)
            self.length -= length
            return data

class EOFReader(IReader):
    def __init__(self, reader):
        self.reader = reader
        self.eof = False

    def read(self, size):
        if self.eof or size == 0:
            return b''
        else:
            data = self.reader.read(size, 1)
            if len(data) < size:
                self.eof = True
            return data
                
class Request:
    def __init__(self, method, uri, version, header, reader):
        self.method = method
        self.uri = uri
        self.version = version
        self.reader = reader
        self._header = header 
        self._body = None
        self.initial_time = time.time()


    @property
    def local_addr(self):
        return self.reader.sock.local_addr

    @property
    def header(self):
        return self._header

    @header.setter
    def header(self, header):
        if not isinstance(header, Header): 
            raise TypeError('{} must be an Header'.format(header))
        self._header = header

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, reader):
        if not isinstance(reader, IReader): 
            raise TypeError('{} must be an IReader'.format(reader))
        self._body = reader
        
    def __enter__(self):
        content_length = self.header.get("Content-Length", int)

        if content_length and content_length < 0:
            raise InvalidHeader("Content-Length")

        chunked = self.header.get("Transfer-Encoding") == 'chunked'
        if chunked:
            self.body = ChunkReader(self.reader)
        elif content_length:
            self.body = LengthReader(self.reader, content_length)
        else:
            self.body = EOFReader(self.reader)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._body = None

    def should_close(self):
        value = self.header.get('Connection')
        if value == 'close':
            return True
        elif value == 'keep-alive':
            return False
        else:
            return self.version <= 'HTTP/1.0'
