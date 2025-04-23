import os
import sys
import time
from datetime import datetime

# Get the current directory and add it to Python path if needed
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Clear any USE_MOCK_DATA environment variables to avoid conflicts
if 'USE_MOCK_DATA' in os.environ:
    del os.environ['USE_MOCK_DATA']
if 'MOCK_REPORT_PATH' in os.environ:
    del os.environ['MOCK_REPORT_PATH']

# Set important environment variables before importing the app
# os.environ['SCRIPT_NAME'] = '/appopvibe' # Let Passenger handle this via PassengerBaseURI
# os.environ['APPLICATION_ROOT'] = '/appopvibe' # Let Passenger handle this via PassengerBaseURI
# Debug mode for development - MUST be false in production
os.environ['FLASK_DEBUG'] = 'false' # Disable Flask debugging for production
# os.environ['SESSION_COOKIE_SECURE'] = 'true' # Let .htaccess or hosting panel handle this

# Server configuration - increase process limits to prevent errors
os.environ['LSAPI_CHILDREN'] = '12'  # Increase from 6 to 12 child processes
os.environ['LSAPI_MAX_IDLE'] = '600'  # Increase max idle time
os.environ['LSAPI_MAX_PROCESS_TIME'] = '600'  # Increase max process time to 600 seconds
# os.environ['GROQ_API_KEY'] = '...' # Let .htaccess or hosting panel handle this

# Import the Flask app after setting environment variables
from app import app as application 

# Create a URL tracing WSGI middleware
class URLTracingMiddleware:
    def __init__(self, app):
        self.app = app
        self.log_path = os.path.join(project_home, 'logs', 'url_trace.log')
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def __call__(self, environ, start_response):
        # Get request information
        path = environ.get('PATH_INFO', '-')
        query = environ.get('QUERY_STRING', '')
        method = environ.get('REQUEST_METHOD', '-')
        ip = environ.get('REMOTE_ADDR', '-')
        user_agent = environ.get('HTTP_USER_AGENT', '-')
        referer = environ.get('HTTP_REFERER', '-')
        
        # Create log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {ip} - {method} {path}"
        if query:
            log_entry += f"?{query}"
        log_entry += f" - Referer: {referer} - User-Agent: {user_agent}\n"
        
        # Write to log file
        try:
            with open(self.log_path, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            # If logging fails, don't break the application
            print(f"Error logging request: {e}")
        
        # Start timer to measure response time
        start_time = time.time()
        
        def custom_start_response(status, headers, exc_info=None):
            # Log response status
            try:
                with open(self.log_path, 'a') as f:
                    duration = time.time() - start_time
                    f.write(f"  Response: {status} ({duration:.3f}s)\n")
            except Exception:
                pass
            return start_response(status, headers, exc_info)
        
        # Pass the request to the actual application
        return self.app(environ, custom_start_response)

# Wrap the application with our middleware
application = URLTracingMiddleware(application)

# Print debug information to help diagnose issues
print("Passenger WSGI script loaded")
print(f"LSAPI_CHILDREN set to: {os.environ.get('LSAPI_CHILDREN', 'Not set')}")
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")

# The variable 'application' is what Passenger looks for by default.