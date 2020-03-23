# -*- coding: utf-8 -*-

import os
import sys
import time
import signal
import errno
import queue
import functools
import logging


from lin.sock import create_socks
from lin.executor import Executor
from lin.utils import daemonize, set_process_owner


logger = logging.getLogger(__name__)

class Arbiter:

    SIGNALS = {}

    def __init__(self, config):
        self.executors = set()
        self.sig_queue = queue.Queue()
        self.config = config

    def setup(self):
        logger.info("Arbiter started")
        logger.info("Listening at: %s", ",".join(['{}:{}'.format(*l) for l in self.config.listen]))

        logger.debug('Current configuration:\n{}'.format(
            '\n'.join(['{}: {}'.format(k, v) for k, v in self.config.items()])
            ))

        if self.config.daemon:
            daemonize(self.config.umask)
        else:
            os.umask(self.config.umask)

        set_process_owner(*self.config.user)

        self.listeners = create_socks(self.config.listen, self.config.backlog)
         

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
        self.reap_executors()

    @_signal.__func__(SIGNALS, signal.SIGTERM)
    def sigterm(self):
        '''quick shutdown'''
        self.finalize_executors(signal.SIGTERM)
        sys.exit()

    @_signal.__func__(SIGNALS, signal.SIGINT)
    def sigint(self):
        '''quick shutdown'''
        self.finalize_executors(signal.SIGINT)
        sys.exit()

    @_signal.__func__(SIGNALS, signal.SIGQUIT)
    def sigquit(self):
        '''graceful shutdown'''
        self.finalize_executors(signal.SIGQUIT)
        sys.exit()

    @_signal.__func__(SIGNALS, signal.SIGHUP)
    def sighup(self):
        '''reload config'''
        self.reload()

    def reload(self):
        '''reload config'''
        #TODO
        pass

    def reap_executors(self):
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if not pid:
                    break

                exitcode = os.WEXITSTATUS(status)
                logger.info('Reap executor with pid: {} exit code: {}'.format(pid, exitcode))

                if pid in self.executors:
                    self.executors.remove(pid)
                    continue
        except OSError as e:
            if e.errno != errno.ECHILD:
                raise

    def spawn_executor(self):
        pid = os.fork()
        if pid != 0:
            return pid
        executor = Executor(self.listeners, self.config)
        executor.run()

    def kill_executor(self, pid, sig):
        try:
            os.kill(pid, sig)
        except ProcessLookupError as e:
            return #ignore

    def initialize_executors(self):
        '''initialize executors'''
        while self.config.processes > len(self.executors):
            pid = self.spawn_executor()
            self.executors.add(pid)

    def finalize_executors(self, sig):
        '''finalize executors'''
        for pid in self.executors.copy():
            if pid in self.executors:
                self.executors.remove(pid)
            self.kill_executor(pid, sig)
            time.sleep(0.1)

    def manage_executors(self):
        '''manage executors'''
        if self.config.processes > len(self.executors):
            self.initialize_executors()

        while self.config.processes < len(self.executors):
            pid = self.executors.pop()
            self.kill_executor(pid, signal.SIGQUIT)
            

    def run(self):
        self.setup()
        self.signal_register()
        self.initialize_executors()
        while True:
            try:
                sig_handler = self.sig_queue.get(timeout = 3)
                sig_handler(self)
            except queue.Empty:
                self.manage_executors()
