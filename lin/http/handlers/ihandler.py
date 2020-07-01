# -*- coding: utf-8 -*-

class IHandler:
    async def handle(self, request, response):
        raise NotImplementedError()

    #TODO
    #def __setattr__(self, attr, value):
    #    raise AttributeError("Property<{}.{}> is read only".format(type(self).__name__, attr))
