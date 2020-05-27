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
        self.loop.create_task(self.worker.process(client))

    async def accept(self, listener):
        while self.alive:
            client, addr = await listener.accept()
            self.handle(client, addr)

    def listen(self):
        for sock in self.socks:
            self.loop.create_task(self.accept(AsyncSocketWrapper(self.loop, sock)))

    def run(self):
        self.listen()
        self.loop.run_forever()
