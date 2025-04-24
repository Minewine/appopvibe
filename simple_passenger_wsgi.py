"""
Absolutely minimal WSGI script with no dependencies
Uses only ASCII characters and avoids any fancy features
"""
import os
import sys

# Basic application that always works
def application(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/html')]
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Basic WSGI App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .success { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Basic WSGI Application</h1>
        <p class="success">SUCCESS: Basic WSGI is working!</p>
        <p>Python version: %s</p>
        <p>Working directory: %s</p>
    </body>
    </html>
    """ % (sys.version, os.getcwd())
    
    start_response(status, response_headers)
    return [html.encode('ascii', 'replace')]

# Print debug information
print("Ultra-simple WSGI script loaded")
print("Python version: " + sys.version)
print("Working directory: " + os.getcwd())