# -*- coding: utf-8 -*-

import os
import time

from lin.http.handlers.ihandler import IHandler
from lin.logger import Logger

class LogHandler(IHandler):
    def __init__(self, access_log='-', access_fmt="{time_local} {status} {request_method} {request_uri} {request_time} {http_user_agent}"):
        self.access_log = access_log
        self.access_fmt = access_fmt
        self.log = Logger(access_log)
        self.log.setup()

    def handle(self, request, response):
        atoms = {
                'remote_addr': response.writer.remote_addr,
                'server_addr': response.writer.local_addr,
                'time_local': time.strftime('[%d/%b/%Y:%H:%M:%S %z]'),
                'request_method': request.method,
                'request_uri': request.uri,
                'request_time': time.time() - request.initial_time,
                'http_user_agent': request.header.get('user-agent'),
                'http_x_forwarded_for':request.header.get('x-forwarded-for') if request.header.get('x-forwarded-for') else '-',
                'http_referer': request.header.get('referer') if request.header.get('referer') else '-',
                'http_host': request.header.get('host') if request.header.get('host') else '-',
                'status': response.status,
                'scheme': 'http',
                'pid': os.getpid(),
                }
        self.log.info(self.access_fmt.format(**atoms))
