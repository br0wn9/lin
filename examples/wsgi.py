
def app(environ, start_response):
    body = b'hello world'
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8'),
            ('Content-Length', len(body))]
    start_response(status, headers)

    return [body]
