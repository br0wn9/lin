# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import errno
import queue
import functools
import logging


from lin.connector import AsyncConnector
from lin.manager import Manager
from lin.utils import daemonize, set_process_owner


logger = logging.getLogger(__name__)

class Arbiter:

    SIGNALS = {}

    def __init__(self, config):
        self.managers = set()
        self.sig_queue = queue.Queue()
        self.config = config

    def setup(self):
        logger.info("Arbiter booting with pid: {}".format(os.getpid()))
        logger.info("Listening at: %s", ",".join(['{}:{}'.format(*l) for l in self.config.listen]))

        logger.debug('Current configuration:\n{}'.format(
            '\n'.join(['{}: {}'.format(k, v) for k, v in self.config.items()])
            ))

        if self.config.daemon:
            daemonize(self.config.umask)
        else:
            os.umask(self.config.umask)

        set_process_owner(*self.config.user)

        self.connectors = [AsyncConnector(endpoint, self.config.backlog) for endpoint in self.config.listen]

    def signal_register(self):
        [signal.signal(sig, self.sig_handler) for sig in self.SIGNALS.keys()]
        signal.signal(signal.SIGCHLD, self.sigchld_handler)

    @staticmethod
    def _signal(signals, sig):
        def signal_decorator(func):
            @functools.wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)
            signals[sig] = handler
            return handler
        return signal_decorator

    def sig_handler(self, sig, frame):
        if self.sig_queue.qsize() < 5:
            self.sig_queue.put(self.SIGNALS[sig])

    def sigchld_handler(self, sig, frame):
        self.reap_managers()

    @_signal.__func__(SIGNALS, signal.SIGTERM)
    def sigterm(self):
        '''quick shutdown'''
        self.finalize_managers(signal.SIGTERM)
        sys.exit()

    @_signal.__func__(SIGNALS, signal.SIGINT)
    def sigint(self):
        '''quick shutdown'''
        self.finalize_managers(signal.SIGINT)
        sys.exit()

    @_signal.__func__(SIGNALS, signal.SIGQUIT)
    def sigquit(self):
        '''graceful shutdown'''
        self.finalize_managers(signal.SIGQUIT)
        sys.exit()

    @_signal.__func__(SIGNALS, signal.SIGHUP)
    def sighup(self):
        '''reload config'''
        self.reload()

    def reload(self):
        '''reload config'''
        #TODO
        pass

    def reap_managers(self):
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if not pid:
                    break

                exitcode = os.WEXITSTATUS(status)
                logger.info("Reap manager with pid: {} exit code: {}".format(pid, exitcode))

                if exitcode == Manager.BOOT_ERROR:
                    logger.warning("Manager failed to boot")
                    sys.exit(-1)

                if pid in self.managers:
                    self.managers.remove(pid)
                    continue
        except OSError as e:
            if e.errno != errno.ECHILD:
                raise

    def spawn_manager(self):
        pid = os.fork()
        if pid != 0:
            return pid
        manager = Manager(self.connectors, self.config)
        manager.run()

    def kill_manager(self, pid, sig):
        try:
            os.kill(pid, sig)
        except ProcessLookupError as e:
            return #ignore

    def initialize_managers(self):
        '''initialize managers'''
        while self.config.processes > len(self.managers):
            pid = self.spawn_manager()
            self.managers.add(pid)

    def finalize_managers(self, sig):
        '''finalize managers'''
        for pid in self.managers.copy():
            if pid in self.managers:
                self.managers.remove(pid)
            self.kill_manager(pid, sig)
            time.sleep(0.1)

    def keep_managers(self):
        '''keep managers'''
        if self.config.processes > len(self.managers):
            self.initialize_managers()

        while self.config.processes < len(self.managers):
            pid = self.managers.pop()
            self.kill_manager(pid, signal.SIGQUIT)
            

    def run(self):
        self.setup()
        self.signal_register()
        self.initialize_managers()
        while True:
            try:
                sig_handler = self.sig_queue.get(timeout = 3)
                sig_handler(self)
            except queue.Empty:
                self.keep_managers()
