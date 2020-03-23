listen = '127.0.0.1:8000'

backlog = 2048

processes = 4

daemon = False

umask = 0o022

user = '_www:staff'

workdir = './examples/'

buffer_size = 8192

error_log = '-', 'info'

limit_request_line = 8192

limit_request_header = 8192

handler = inject('lin.http.handlers.chainhandler:ChainHandler',
        handlers = [
            inject('lin.http.handlers.wsgihandler:WSGIHandler',
                application='wsgi:application'
                ),
            inject('lin.http.handlers.loghandler:LogHandler',
                access_log='access.log',
                ),
            ]
        )
