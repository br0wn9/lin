# -*- coding: utf-8 -*-

import asyncio

from lin.sock import AsyncSocketWrapper

class Accepter:
    def __init__(self, loop, socks, worker, conf):
        self.socks = socks
        self.worker = worker 
        self.conf = conf
        self.loop = loop
        self.alive = True

    def exit(self):
        self.alive = False

    def handle(self, client, addr):
        self.loop.create_task(self.worker.process(client, addr))

    async def accept(self, listener):
        while self.alive:
            client, addr = await listener.accept()
            self.handle(client, addr)

    def listeners(self):
        return [self.accept(AsyncSocketWrapper(self.loop, sock)) for sock in self.socks]

    def run(self):
        listeners = self.listeners()
        self.loop.run_until_complete(asyncio.wait(listeners))
