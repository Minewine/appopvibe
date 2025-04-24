"""
CV Analyzer - Application Entry Point

This is the main entry point for the CV Analyzer application.
It creates an application instance using the factory pattern.
"""
import os
from appopvibe import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Looking for .env file at: {dotenv_path}")
if os.path.exists(dotenv_path):
    print(f".env file found at: {dotenv_path}")
else:
    print(f"WARNING: .env file not found at: {dotenv_path}")
    # Try looking in the project root directory
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    print(f"Trying alternative path: {dotenv_path}")

# Force override existing environment variables with .env values
load_dotenv(dotenv_path=dotenv_path, verbose=True, override=True)

# Verify if key environment variables are loaded
groq_key = os.getenv('GROQ_API_KEY')
if groq_key:
    print(f"GROQ_API_KEY loaded successfully (length: {len(groq_key)})")
else:
    print("✗ ERROR: Missing GROQ_API_KEY environment variable")
    print("Please set the GROQ_API_KEY in your .env file or environment variables")
    # Exit if running as a script
    if __name__ == '__main__':
        import sys
        sys.exit(1)

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Run the app with debug=True and display the URL
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)