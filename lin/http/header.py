# -*- coding: utf-8 -*-

from lin.utils import str_to_bytes

class Header:
    def __init__(self, fields = None):
        self._fields = fields if fields else []

    def _get(self, key):
        key = key.lower()
        for k, v in self._fields:
            if k.lower() == key:
                return v

    def get_all(self, key):
        key = key.lower()
        return [v for k, v in self._fields if k.lower() == key]

    def get(self, key, type = None, default = None):
        rv = self._get(key)
        if rv:
            if type is not None:
                try:
                    rv = type(rv)
                except ValueError:
                    rv = default
            return rv
        return default

    def set(self, key, value):
        self._fields.append((key, value))

    def update(self, fields):
        self._fields += fields

    def delete(self, key):
        key = key.lower()
        self._fields = [field for field in self._fields if key != field[0].lower()]

    def to_bytes(self):
        return str_to_bytes('\r\n'.join(['{}: {}'.format(*field) for field in self._fields]) + '\r\n\r\n')

    def __iter__(self):
        yield from self._fields
