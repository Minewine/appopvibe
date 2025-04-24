def application(environ, start_response):
    status = '200 OK'
    output = b'Python 3.9.21 test application is working!'
    
    response_headers = [
        ('Content-type', 'text/plain'),
        ('Content-Length', str(len(output)))
    ]
    
    start_response(status, response_headers)
    return [output]