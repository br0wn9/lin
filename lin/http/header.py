from lin.utils import str_to_bytes

class Header:
    def __init__(self, fields = None):
        self.fields = fields if fields else []

    def _get(self, key):
        for k, v in self.fields:
            if k.lower() == key.lower():
                return v

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
        self.fields.append((key, value))

    def update(self, fields):
        self.fields += fields

    def to_bytes(self):
        return str_to_bytes('\r\n'.join(['{}: {}'.format(*field) for field in self.fields]) + '\r\n\r\n')

    def __iter__(self):
        yield from self.fields
