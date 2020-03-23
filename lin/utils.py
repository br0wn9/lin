# -*- coding: utf-8 -*-

import os
import os.path
import sys
import traceback
import email.utils
import time
import asyncio
import functools

import importlib


def bytes_to_str(b):
    """Converts a byte string argument to a string"""
    if isinstance(b, str):
        return b
    return str(b, 'latin1')

def str_to_bytes(value, encoding="utf8"):
    """Converts a string argument to a byte string"""
    if isinstance(value, bytes):
        return value
    if not isinstance(value, str):
        raise TypeError('%r is not a string' % value)

    return value.encode(encoding)

def http_date(timestamp=None):
    """Return the current date and time formatted for a message header"""
    if timestamp is None:
        timestamp = time.time()
    s = email.utils.formatdate(timestamp, localtime=False, usegmt=True)
    return s

def get_task_id():
    """Return the current task identify"""
    return id(asyncio.current_task())

def set_process_workdir(root):
    """ set workdir of processes """
    # set process root dir 
    os.chdir(root)

    # add the path to sys.path
    sys.path.insert(0, root)

def set_process_owner(uid, gid):
    """ set user and group of processes """
    if gid:
        os.setgid(gid)

    if uid:
        os.setuid(uid)

class LazyFunction:
    __slots__ = ('func', 'kwargs', '_instance')

    def __init__(self, func, **kwargs):
        self.func = func
        self.kwargs = kwargs
        self._instance = None

    def __getattr__(self, attr):
        if self._instance is None:
            self._instance = self.func(**self.kwargs)
        return getattr(self._instance, attr)

    def __str__(self):
        return "<Lazy {}.{}>".format(self.func.__module__, self.func.__name__)

    def __repr__(self):
        return self.__str__()

    def __call__(self, *args, **kwargs):
        if self._instance is None:
            self._instance = self.func(**self.kwargs)
        return self._instance(*args, **kwargs)
    
def load_symbol(symbol):
    sep = ':' if ':' in symbol else '.'
    module_name, _, cls_name = symbol.rpartition(sep)
    if not module_name:
        raise ValueError("Invalid symbol %s" % symbol)

    module = importlib.import_module(module_name)
    return getattr(module, cls_name)

def inject(name, **kwargs):
    cls = load_symbol(name)

    return LazyFunction(cls, **kwargs)

def exec_file(filename, globals, locals):
    with open(filename, 'r') as fp:
        co = compile(fp.read(), filename, 'exec')
    return exec(co, globals, locals)

def load_config(filename):
    cfg = {
            '__doc__': 'config',
            '__builtins__': __builtins__,
            '__name__': '__config__',
            '__file__': filename,
            'inject': inject,
            }
    try:
        if not os.path.exists(filename):
            raise RuntimeError("The configuration file does not exist: %s" % filename)

        exec_file(filename, cfg, cfg)
    except Exception:
        sys.stderr.write('Failed to load configuration file: %s\n' % filename)
        traceback.print_exc()
        sys.exit(-1)

    return cfg


def daemonize(umask):
    """
    Do the UNIX double-fork magic, see Stevens' "Advanced
    Programming in the UNIX Environment" for details (ISBN 0201563177)
    http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
    """
    try:
        pid = os.fork()
        if pid > 0:
            # Exit first parent
            os._exit(0)
    except OSError as e:
        sys.stderr.write(
            "fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        os._exit(1)

    # Decouple from parent environment
    os.setsid()
    os.umask(umask)

    # Do second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from second parent
            ox._exit(0)
    except OSError as e:
        sys.stderr.write(
            "fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        os._exit(1)
