# -*- coding: utf-8 -*-

import asyncio

class Accepter:
    def __init__(self, connectors, worker, max_conn, loop):
        self.connectors = connectors
        self.worker = worker 
        self.loop = loop
        self.sem = asyncio.BoundedSemaphore(max_conn)
        self.alive = True

    def exit(self):
        self.alive = False
        for connector in self.connectors:
            connector.close()

    def handle(self, client, addr):
        task = self.loop.create_task(self.worker.process(client))
        task.add_done_callback(lambda r: self.sem.release())

    async def accept(self, connector):
        while self.alive:
            await self.sem.acquire()
            client, addr = await connector.accept()
            self.handle(client, addr)

    def setup(self):
        for connector in self.connectors:
            connector.open(self.loop)
            self.loop.create_task(self.accept(connector))

    def run(self):
        self.setup()
        self.loop.run_forever()
