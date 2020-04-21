# -*- coding: utf-8 -*-

import os
import os.path
import hashlib
import mimetypes

from urllib.parse import unquote

from lin.utils import http_date, str_to_bytes
from lin.http.handlers.ihandler import IHandler
from lin.http.response import Response, IWriter

class StaticHandler(IHandler):
    def __init__(self, location, root):
        self.location = location
        self.root = root

    def loader(self, path_info):
        filepath = path_info[len(self.location):]
        filename = os.path.join(self.root, filepath)
        stats = os.stat(filename)

        return open(filename, 'rb'), filename, stats.st_mtime, stats.st_size

    def except_handle(self, response, http_code, http_message):
        response.set_status('{} {}'.format(http_code, http_message))
        response.header.set('Content-Type', 'text/plain')
        response.header.set('Content-Length', str(len(http_message)))
        response.body.set_content([str_to_bytes(http_message)])

    def handle(self, request, response):
        path_info = unquote(request.uriparts.path, 'latin1')

        if path_info.startswith(self.location):
            try:
                fd, filename, mtime, size = self.loader(path_info)

                mime_type, encoding = mimetypes.guess_type(filename)
                mime_type if mime_type else 'text/plain'

                etag = '{}:{}:{}'.format(mtime, size, filename)

                response.set_status('200 OK')
                response.header.set('Content-Type', mime_type)
                response.header.set('Content-Length', str(size))
                response.header.set('Last-Modified', http_date(mtime))
                response.header.set('Etag', hashlib.sha1(str_to_bytes(etag)).hexdigest())

                response.body.set_file(fd)

            except (FileNotFoundError, IsADirectoryError):
                self.except_handle(response, 404, 'Not Found')
                
            except PermissionError:
                self.except_handle(response, 403, 'Forbidden')
        else:
            self.except_handle(response, 404, 'Not Found')
