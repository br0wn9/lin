# -*- coding: utf-8 -*-

import socket

from lin.sock import AsyncSocketWrapper

class AsyncConnector:
    def __init__(self, endpoint, backlog):
        self.backlog = backlog
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(endpoint)

    def open(self, loop):
        self._loop = loop
        self._sock.listen(self.backlog)
        self._sock.setblocking(False)

    @classmethod
    def create(cls, endpoint, backlog, loop):
        connector = cls(endpoint, backlog)
        connector.open(loop)
        return connector

    async def accept(self):
        sock, address = await self._loop.sock_accept(self._sock)
        return AsyncSocketWrapper(self._loop, sock), address

    def close(self):
        self._sock.close()
