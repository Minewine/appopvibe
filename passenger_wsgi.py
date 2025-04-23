import os
import sys

# Get the current directory and add it to Python path if needed
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set important environment variables before importing the app
os.environ['SCRIPT_NAME'] = '/appopvibe'
os.environ['APPLICATION_ROOT'] = '/appopvibe'
os.environ['USE_MOCK_DATA'] = 'true'  # Force using mock data to avoid API issues
os.environ['SESSION_COOKIE_SECURE'] = 'true'  # Secure cookies with HTTPS

# Import the Flask app after setting environment variables
from app import app as application 

# The variable 'application' is what Passenger looks for by default. new