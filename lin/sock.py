# -*- coding: utf-8 -*-

import asyncio
import io
import socket, select, errno

class AsyncSocketWrapper:
    def __init__(self, loop, sock):
        self._loop = loop
        self._sock = sock

    @property
    def local_addr(self):
        return self._sock.getsockname()

    @property
    def remote_addr(self):
        return self._sock.getpeername()

    def blocking_write(self, data):
        length = len(data)
        while length:
            try:
                sent = self._sock.send(data)
            except BlockingIOError as e:
                select.select([], [self._sock], [])
                continue
            data = data[sent:]
            length -= sent

    def blocking_read(self, size, timeout=None):
        data = b''
        while True:
            try:
                part = self._sock.recv(size)
                if len(part) == 0:
                    return data
                elif len(part) < size:
                    data += part
                    size -= len(part)
                    continue
                else:
                    return data + part

            except BlockingIOError as e:
                rlist, _, _ = select.select([self._sock], [], [], timeout)
                if rlist:
                    continue
                else:
                    return data

    def close(self):
        self._loop.remove_reader(self._sock.fileno())
        self._sock.close()

    def shutdown(self):
        self._sock.shutdown(socket.SHUT_RDWR)

    async def recv_timeout(self, nbytes, timeout):
        return await asyncio.wait_for(self.recv(nbytes), timeout=timeout) if timeout else await self.recv(nbytes)

    async def recv(self, nbytes):
        return await self._loop.sock_recv(self._sock, nbytes)

    async def recv_into(self, buf):
        return await self._loop.sock_recv_into(self._sock, buf)

    async def sendall(self, data):
        return await self._loop.sock_sendall(self._sock, data)

    async def connect(self, address):
        return await self._loop.sock_connect(self._sock, address)

    async def accept(self):
        sock, address = await self._loop.sock_accept(self._sock)
        return AsyncSocketWrapper(self._loop, sock), address

    async def sendfile(self, file, offset=0, count=None, *, fallback=True):
        return await self._loop.sock_sendfile(self._sock, file, offset, count, fallback=fallback)
