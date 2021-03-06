# -*- coding: utf-8 -*-

import os
import sys
import signal

import asyncio
import logging
import functools

from lin.accepter import Accepter
from lin.worker import Worker

logger = logging.getLogger(__name__)

class Manager:

    BOOT_ERROR = 128

    def __init__(self, connectors, config):
        self.connectors = connectors
        self.config = config
        self.loop = asyncio.get_event_loop()
        self.setup()

    def setup(self):
        self.accepter = Accepter(self.connectors, Worker(self.config), self.config.connections, self.loop)

    @property
    def pid(self):
        return os.getpid()

    def exit(self, error):
        self.accepter.exit()
        sys.exit(error)

    def reload(self):
        '''reload config'''
        #TODO
        pass

    def sigquit_handler(self):
        '''graceful shutdown'''
        self.exit(1)

    def sigint_handler(self):
        '''quick shutdown'''
        self.exit(0)

    def sighup_handler(self):
        '''reload config'''
        self.reload()

    def sigterm_handler(self):
        '''quick shutdown'''
        self.exit(1)

    def init_signals(self):
        self.loop.add_signal_handler(signal.SIGQUIT, self.sigquit_handler)
        self.loop.add_signal_handler(signal.SIGHUP, self.sighup_handler)
        self.loop.add_signal_handler(signal.SIGINT, self.sigint_handler)
        self.loop.add_signal_handler(signal.SIGTERM, self.sigterm_handler) 

    def run(self):
        logger.info("Manager booting with pid: {}".format(self.pid))
        self.init_signals()
        self.accepter.run()

        logger.info("Manager exiting with pid: {}".format(self.pid))
        self.exit(self.BOOT_ERROR)

    def __str__(self):
        return "<Manager {}>".format(self.pid)

