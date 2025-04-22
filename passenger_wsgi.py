import os
import sys

# Assuming your main Flask file is app.py and the Flask app instance is named 'app'
from app import app as application

# Optional: Add project directory to path if needed, but cPanel often handles this.
# project_home = '/home/your_cpanel_username/appopvibe' # Adjust if necessary on server
# if project_home not in sys.path:
#     sys.path.insert(0, project_home)

# Optional: Set environment variables here if not using cPanel UI
# os.environ['FLASK_ENV'] = 'production'
os.environ['SCRIPT_NAME'] = '/appopvibe'

# The variable 'application' is what Passenger looks for by default.