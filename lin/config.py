# -*- coding: utf-8 -*-

import os
import pwd
import grp
import multiprocessing

from lin.utils import LazyFunction, set_process_workdir

from lin.http.handlers.ihandler import IHandler

class InvalidUserGroupException(Exception):
    def __init__(self, user):
        self.user = user

    def __str__(self):
        return "Invalid user:group: %s" % self.user

class Config(type):

    SETTINGS = []

    def __new__(cls, name, bases, attrs):
        setting = super().__new__(cls, name, bases, attrs)
        if setting.name: cls.SETTINGS.append(setting)
        return setting

    @classmethod
    def parse(cls, cfg):
        settings = Settings()
        set_process_workdir(cfg.get('workdir'))
        for setting in cls.SETTINGS:
            value = cfg.get(setting.name)
            if value is None and setting.default is None:
                raise ValueError("%s a is required" % setting.name)
            elif value is None:
                value = setting.default
            else:
                value = setting.validator(value)
            settings.set(setting.name, value)

        return settings

            
        
class Settings(dict):
    def get(self, attr):
        return self[attr]

    def set(self, attr, value):
        self[attr] = value

    def __getattr__(self, attr):
        if attr not in self:
            raise AttributeError("No setting for: %s" % attr)
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

def uint_validator(value):
    if not isinstance(value, int):
        raise TypeError("Not a int: %s" % value)
    if value < 0:
        raise ValueError("Must be a positive int: %d" % value)
    return value

def string_validator(value):
    if not isinstance(value, str):
        raise TypeError("Not a string: %s" % value)
    return value

def bool_validator(value):
    if not isinstance(value, bool):
        raise TypeError("Not a bool: %s" % value)
    return value

def string2endpoint(s):
    addr, port = s.rsplit(':', 1)
    return addr, int(port)

def listen_validator(value):
    if isinstance(value, str):
        return [string2endpoint(value)]
    elif isinstance(value, tuple):
        return [string2endpoint(v) for v in value]
    else:
        raise TypeError("Not a string or tuple: %s" % value)

def error_log_validator(value):
    if isinstance(value, str):
        return (value, 'info')
    elif isinstance(value, tuple) and len(value) == 2 and \
            isinstance(value[0], str) and isinstance(value[1], str):
        return value
    else:
        raise TypeError("Not a string or tuple: %s" % value)

def handler_validator(value):
    if not isinstance(value, LazyFunction) and not issubclass(value.func, IHandler):
        raise TypeError("Not a inject handler: %s" % str(value))
    return value

def user_validator(value):
    if isinstance(value, str):
        user = value.split(':', 1)
        if len(user) != 2:
            raise InvalidUserGroupException(value)
        try:
            return pwd.getpwnam(user[0]).pw_uid, grp.getgrnam(user[1]).gr_gid
        except KeyError:
            raise InvalidUserException(value)
    else:
        raise TypeError("Not a string: %s" % value)

class Setting(metaclass=Config):
    '''
        abstract setting
    '''

    name = None
    default = None
    validator = None

class Listen(Setting):
    '''
        The listening address of the service
    '''

    name = 'listen'
    default = ('127.0.0.1', 9000) 
    validator = listen_validator

class Backlog(Setting):
    '''
        The maximum number of pending connections.
    '''

    name = 'backlog'
    default = 1024
    validator = uint_validator

class Processes(Setting):
    '''
        The number of worker processes.
    '''

    name = 'processes'
    default = multiprocessing.cpu_count()
    validator = uint_validator

class Connections(Setting):
    '''
        The maximum number of connections.
    '''

    name = 'connections'
    default = 65535
    validator = uint_validator

class Workdir(Setting):
    '''
        The working directory of the application.
    '''

    name = 'workdir'
    default = '.'
    validator = string_validator

class Daemon(Setting):
    '''
        Detaches the processes from the controlling terminal.
    '''

    name = 'daemon'
    default = False
    validator = bool_validator

class Keepalive(Setting):
    '''
        The number of seconds to wait for request.
    '''

    name = 'keepalive_timeout'
    default = 60
    validator = uint_validator

class User(Setting):
    '''
        Switch  processes to run as this user and group.
    '''

    name = 'user'
    default = (os.geteuid(), os.getegid())
    validator = user_validator

class Umask(Setting):
    '''
        A bit mask for the file mode.
    '''

    name = 'umask'
    default = 0o022
    validator = uint_validator

class ErrorLog(Setting):
    '''
        The error log path and level.
    '''

    name = 'error_log'
    default = ('-', 'info')
    validator = error_log_validator

class BufferSize(Setting):
    '''
        The maximum size of read buffer.
    '''

    name = 'buffer_size'
    default = 8192
    validator = uint_validator

class LimitRequestLine(Setting):
    '''
        The maximum size of HTTP request line.
    '''

    name = 'limit_request_line'
    default = 8192
    validator = uint_validator

class LimitRequestHeader(Setting):
    '''
        The maximum size of HTTP request header.
    '''

    name = 'limit_request_header'
    default = 8192
    validator = uint_validator

class Sendfile(Setting):
    '''
        Disable the use of sendfile.
    '''

    name = 'sendfile'
    default = False
    validator = bool_validator

class Handler(Setting):
    '''
        The handler
    '''

    name = 'handler'
    validator = handler_validator
