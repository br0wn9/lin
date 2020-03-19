Lin
----

Lin is a high performance and scalable Python HTTP Server. Base on Python

asyncio library, Easy to extensions and Easy to use.

** NOTE: Werkzeug WSGI-based frameworks are not currently supported(in development) **


Documentation
-------------

In development

Requirements
------------

lin requires Python 3.x >= 3.6.

lin supports Linux, Freebsd, and MacOS


Installation
------------

Install from pypi::

    $ pip install -U lin

Install from source::

    $ python setup.py install
 

Usage
------

Simple wsgi application:

.. code:: python
    
    def application(environ, start_response):
        body = b'hello world'
        status = '200 OK'
        headers = [('Content-type', 'text/plain; charset=utf-8'), ('Content-Length', len(body))]
        start_response(status, headers)
        return [body]

Basic usage::
    $ lin -c config.py


Configuration
-------------

For example:

.. code:: python

    listen = '127.0.0.1:8000'
    backlog = 4
    processess = 4
    error_log = '-', 'info'
    handler = inject('lin.http.handlers.chainhandler:ChainHandler',
            handlers = [
                inject('lin.http.handlers.wsgihandler:WSGIHandler',
                    application='testapp:application' #application path
                    ),
                inject('lin.http.handlers.loghandler:LogHandler',
                    access_log='access.log',  # access log path
                    ),
                ]
            )

Extension
---------

For example:

.. code:: python

    from lin.http.handlers.ihandler import IHandler

    class ExampleHandler(IHandler):

        def handle(self, request, response):
            # processing request and response

License
-------

Lin is released under the BSD License. See the LICENSE file for more details.
