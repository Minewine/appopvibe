"""
Simple test Flask application to verify import and setup works
"""
import os
from flask import Flask

# Create test application
app = Flask(__name__)

@app.route('/')
def index():
    return 'Basic Flask app is working! This confirms the import mechanism is correct.'

if __name__ == '__main__':
    app.run(debug=False)