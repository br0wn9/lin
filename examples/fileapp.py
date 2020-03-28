import os

def app(environ, start_response):
    f = open('/var/log/messages', 'rb')

    fp = f.fileno()
    
    size = os.fstat(fp).st_size
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8'),
            ('Content-Length', str(size))]
    start_response(status, headers)

    return environ['wsgi.file_wrapper'](f)
