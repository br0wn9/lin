

class Header:
    def __init__(self, fields = []):
        self.fields = fields 

    def get(self, key):
        for k, v in self.fields:
            if k.lower() == key.lower():
                return v

    def set(self, key, value):
        self.fields.append((key, value))

    def update(self, fields):
        self.fields += fields

    def dump(self):
        return '\r\n'.join(['{}: {}'.format(*field) for field in self.fields]) + '\r\n\r\n'

    def __iter__(self):
        yield from self.fields
