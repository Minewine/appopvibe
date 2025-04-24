import os
import sys
import time
from datetime import datetime

# Get the current directory and add it to Python path if needed
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Ensure logs directory exists
logs_dir = os.path.join(project_home, 'logs')
if not os.path.exists(logs_dir):
    try:
        os.makedirs(logs_dir)
    except:
        pass

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

# Basic application for testing
def simple_app(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [b'AppOpVibe is starting up. If you see this message, WSGI is working.']

try:
    # Try to import the Flask app - add compatibility for Python 3.9.21
    print("Attempting to import Flask application...")
    
    # Check for critical packages
    try:
        import flask
        print(f"Flask version: {flask.__version__}")
    except ImportError as e:
        print(f"ERROR: Flask not installed properly: {e}")
        raise
        
    # Check for app.py file
    app_path = os.path.join(project_home, 'app.py')
    if not os.path.exists(app_path):
        print(f"ERROR: app.py not found at {app_path}")
        raise FileNotFoundError(f"app.py not found at {app_path}")
    else:
        print(f"Found app.py at {app_path}")
    
    # Explicitly set PYTHONPATH to help with imports
    print(f"Current sys.path: {sys.path}")
    
    # Try alternative import methods if needed
    try:
        # First try importing from the minimal app to verify Flask works
        print("Trying to import from minimal app first...")
        mini_app_path = os.path.join(project_home, 'mini_app.py')
        if os.path.exists(mini_app_path):
            print(f"Found minimal app at {mini_app_path}")
            try:
                from mini_app import app as application
                print("Minimal Flask application successfully imported!")
                # Skip trying to import the other apps since this one worked
                imported_successfully = True
                # Break out of the import chain
                raise ImportError("Using minimal app instead")
            except Exception as e:
                print(f"Minimal app import failed: {e}")
                imported_successfully = False
        
        # If minimal app failed, try the test app
        if not imported_successfully:
            print("Trying to import from test app...")
            test_app_path = os.path.join(project_home, 'app_test.py')
            if os.path.exists(test_app_path):
                print(f"Found test app at {test_app_path}")
                try:
                    from app_test import app as application
                    print("Test Flask application successfully imported!")
                    # Skip trying to import the main app
                    imported_successfully = True
                    # Break out of the import chain
                    raise ImportError("Using test app instead")
                except Exception as e:
                    print(f"Test app import failed: {e}")
                    imported_successfully = False
        
        # If test import failed or file doesn't exist, try the real app
        print("Trying to import from main app...")
        # Try direct import
        from app import app as application
        print("Main Flask application successfully imported")
    except ImportError as e:
        print(f"Direct import failed: {e}")
        # Try using relative import
        print("Trying alternative import method...")
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        application = app_module.app
        print("Flask application imported using importlib")
except Exception as e:
    # If there's an error importing the app, use the simple app and log the error
    error_message = f"Error importing Flask application: {e}"
    print(error_message)
    
    # Get formatted traceback for more detailed error information
    import traceback
    tb = traceback.format_exc()
    
    # Log the error to a file for debugging with full traceback
    error_log_path = os.path.join(project_home, 'logs', 'import_error.log')
    try:
        with open(error_log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] {error_message}\n")
            f.write(f"FULL TRACEBACK:\n{tb}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Working directory: {os.getcwd()}\n")
            f.write(f"sys.path: {sys.path}\n")
            
            # Check for Python package versions that might be causing issues
            try:
                import flask
                f.write(f"Flask version: {flask.__version__}\n")
            except:
                f.write("Flask not properly installed\n")
                
            try:
                import werkzeug
                f.write(f"Werkzeug version: {werkzeug.__version__}\n")
            except:
                f.write("Werkzeug not properly installed\n")
            
            f.write("\n\n")
    except Exception as log_error:
        print(f"Failed to log error: {log_error}")
    
    # Create simple HTML response with error details to make debugging easier - ASCII only
    error_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AppOpVibe - Setup Issue</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            pre {{ background: #f6f8fa; padding: 15px; border-radius: 5px; overflow: auto; }}
            .error {{ color: #d63031; }}
            .info {{ color: #0984e3; }}
        </style>
    </head>
    <body>
        <h1>AppOpVibe - Application Setup Issue</h1>
        <p>The application is running in diagnostic mode.</p>
        <p class="error"><strong>Error:</strong> {str(error_message).encode('ascii', 'replace').decode('ascii')}</p>
        <h3>Diagnostic Information:</h3>
        <pre>Python: {sys.version}
Working Dir: {os.getcwd()}
Timestamp: {datetime.now()}
        </pre>
        <p>Detailed error logs are available in: {error_log_path}</p>
    </body>
    </html>
    """
    
    # Use a modified simple_app that returns HTML with error details
    def diagnostic_app(environ, start_response):
        status = '200 OK'
        response_headers = [('Content-type', 'text/html')]
        start_response(status, response_headers)
        return [error_html.encode('utf-8')]
    
    print("Using diagnostic application instead")
    application = diagnostic_app

# Create a URL tracing WSGI middleware
class URLTracingMiddleware:
    def __init__(self, app):
        self.app = app
        self.log_path = os.path.join(project_home, 'logs', 'url_trace.log')
        
        # Ensure log directory exists
        log_dir = os.path.dirname(self.log_path)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception as e:
                print(f"Failed to create log directory: {e}")
    
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

# Try to wrap the application with our middleware, but provide a fallback
try:
    application = URLTracingMiddleware(application)
    print("URL tracing middleware applied successfully")
except Exception as e:
    print(f"Error applying URL tracing middleware: {e}")
    # Ensure the application variable is still set properly
    print("Using application without middleware")

# Print debug information to help diagnose issues
print("Passenger WSGI script loaded")
print(f"Python version: {sys.version}")
print(f"LSAPI_CHILDREN set to: {os.environ.get('LSAPI_CHILDREN', 'Not set')}")
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")

# The variable 'application' is what Passenger looks for by default.