"""
Ultra-simple passenger_wsgi.py that only imports mini_app
Contains no Unicode characters whatsoever for maximum compatibility
"""
import os
import sys

# Get the current directory and add it to Python path if needed
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Debug mode for development - MUST be false in production
os.environ['FLASK_DEBUG'] = 'false'

# Basic application for testing in case imports fail
def simple_app(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b'AppOpVibe simple fallback is running.']

# Very simple import logic using only ASCII characters
try:
    # Try to import from mini_app.py
    from mini_app import app as application
    print("Mini app successfully imported")
except Exception as e:
    # Fall back to simple app
    error_str = str(e).encode('ascii', 'replace').decode('ascii')
    print("Error importing mini_app: " + error_str)
    application = simple_app

# The variable 'application' is what Passenger looks for by default
print("Simple passenger_wsgi.py loaded")