# -*- coding: utf-8 -*-

import sys
import logging
import itertools

from io import BytesIO
from urllib.parse import urlsplit

from lin.utils import bytes_to_str, str_to_bytes, http_date
from lin.http.handlers.ihandler import IHandler
from lin.http.response import Response, IWriter

from lin.utils import load_symbol

logger = logging.getLogger(__name__)

class WSGIReader:
    def __init__(self, reader):
        self.reader = reader
        self.buff = BytesIO()

    def read(self, size=None):
        if not isinstance(size, int):
            raise TypeError("size must be an integral type") 

        if size is None or size < 0:
            size =  sys.maxsize

        data = self.buff.getvalue()
        if len(data) == 0:
            return self.reader.read(size)
        else:
            remain_data = self.reader.read(size - len(data))
            self.buff = BytesIO()
            return data + remain_data


    def readline(self, size = None):
        while True:
            data = self.buff.getvalue()
            idx = data.find(b'\n')
            if idx > 0:
                self.buff = BytesIO()
                self.buff.write(data[idx:])
                return data[:idx]
            part = self.reader.read(1024)
            if len(part) == 0:
                self.buff = BytesIO()
                return data
            self.buff.write(part)

    def readlines(self, hint = None):
        lines = []
        while True:
            line = self.readline()
            if line:
                lines.append(line)
            else:
                return lines

    def __iter__(self):
        return self

    def __next__(self):
        ret = self.readline()
        if not ret:
            raise StopIteration()
        return ret

class WSGIError:
    def __init__(self, log):
        self.log = log

    def flush(self):
        pass

    def write(self, s):
        self.log.error(s)

    def writelines(self, seq):
        for s in seq:
            self.write(s)

class FileWrapper(IWriter):
    def __init__(self, filelike, blksize=8192):
        self.filelike = filelike
        self.blksize = blksize

    def tell(self):
        if hasattr(self.filelike, 'tell'):
            return self.filelike.tell()
        else:
            return super().tell()

    def fileno(self):
        if hasattr(self.filelike, 'fileno'):
            return self.filelike.fileno()
        else:
            return super().fileno()

    def __iter__(self):
        while True:
          part = self.filelike.read(self.blksize)
          if not part:
              return
          yield part

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()


class WSGIHandler(IHandler):

    def __init__(self, application):
        self.app = load_symbol(application)

    def default_environ(self):
        return {
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'http',
                'wsgi.multithread': False,
                'wsgi.multiprocess': True,
                'wsgi.run_once': False,
                'wsgi.file_wrapper': FileWrapper,
                }

    def environ_create(self, request):
        uriparts = urlsplit(request.uri)
        environ = self.default_environ()
        environ.update(
                {
                    'wsgi.input': WSGIReader(request.body),
                    'wsgi.errors': WSGIError(logger),
                    'REQUEST_METHOD': request.method,
                    'PATH_INFO': uriparts.path,
                    'QUERY_STRING': uriparts.query,
                    'SERVER_NAME': request.local_addr[0],
                    'SERVER_PORT': str(request.local_addr[1]),
                    'SERVER_PROTOCOL': request.version,
                    'SCRIPT_NAME': ''
                    }
                )

        for field in request.header:
            if field[0].upper() == 'CONTENT-TYPE':
                environ['CONTENT_TYPE'] = field[1]
            elif field[0].upper() == 'CONTENT-LENGTH':
                environ['CONTENT_LENGTH'] = field[1]
            else:
                environ['HTTP_{}'.format(field[0])] = field[1]

        return environ


    def wsgi_create(self, req, resp):
        environ = self.environ_create(req)
        def start_response(status, headers, exc_info=None):
            if exc_info:
                try:
                    if resp.header_sent:
                        raise exc_info[1].with_traceback(exc_info[2])
                finally:
                    exc_info = None
            elif not resp.status is None:
                raise AssertionError("response header already set")

            resp.status = status
            resp.header.update(headers)

            return resp.body.write

        return environ, start_response

    def handle(self, request, response):
        environ, start_response = self.wsgi_create(request, response)
        bodyiter = self.app(environ, start_response)
        if isinstance(bodyiter, FileWrapper):
            response.body = bodyiter
        else:
            response.body(bodyiter)
