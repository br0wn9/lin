listen = '127.0.0.1:8000'

backlog = 2048

daemon = False

umask = 0o022

user = '_www:staff'

workdir = './examples/'

keepalive_timeout = 3

buffer_size = 8192

error_log = '-', 'debug'

limit_request_line = 8192

limit_request_header = 8192

sendfile = True

handler = inject('lin.http.handlers.chainhandler:ChainHandler',
        handlers = [
            inject('lin.http.handlers.wsgihandler:WSGIHandler',
                application='wsgi:app'
                ),
            inject('lin.http.handlers.loghandler:LogHandler',
                access_log='access.log',
                ),
            ]
        )
