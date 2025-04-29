import os
import sys
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

# Set important environment variables before importing the app
os.environ['FLASK_DEBUG'] = 'false'  # Disable Flask debugging for production

try:
    # Try to import the Flask app
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

    # Import the main Flask application
    from app import app as application
    print("Main Flask application successfully imported")

except Exception as e:
    # If there's an error importing the app, log the error and use a diagnostic app
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
    except Exception as log_error:
        print(f"Failed to log error: {log_error}")

    # Create a simple diagnostic app
    def diagnostic_app(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [b"An error occurred while starting the application. Check the logs for details."]

    application = diagnostic_app

# Print debug information to help diagnose issues
print("Passenger WSGI script loaded")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")
print(f"Working directory: {os.getcwd()}")