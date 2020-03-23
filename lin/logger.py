# -*- coding: utf-8 -*-

import logging
import time

def logger_setup(filename, verbosity):
    level={
            "critical": logging.CRITICAL,
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
            "debug": logging.DEBUG
            }[verbosity.lower()]

    error_fmt = "%(asctime)s [%(process)d] [%(levelname)s] %(message)s"
    datefmt = "[%Y-%m-%d %H:%M:%S %z]"

    kwargs = {'level': level, 'format': error_fmt, 'datefmt': datefmt}

    if filename != '-':
        kwargs['filename'] = filename

    logging.basicConfig(**kwargs)

class Logger:
    LEVELS = {
            "critical": logging.CRITICAL,
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
            "debug": logging.DEBUG
            }

    def __init__(self, filename):
        self._log = logging.getLogger(filename)
        self.filename = filename

    def remove_handlers(self):
        for h in self._log.handlers:
            self._log.removeHandler(h)

    def setup(self, level = 'info', format="%(message)s", datefmt="[%Y-%m-%d %H:%M:%S %z]"):
        self._log.propagate = False
        self._log.setLevel(self.LEVELS[level.lower()])
        self.remove_handlers()
        handler = logging.StreamHandler() if self.filename == '-' else logging.FileHandler(self.filename)
        handler.setFormatter(logging.Formatter(format, datefmt))
        self._log.addHandler(handler)

    def critical(self, msg, *args, **kwargs):
        self._log.critical(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log.error(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log.warning(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log.info(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log.debug(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log.exception(msg, *args, **kwargs)
