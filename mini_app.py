"""
Minimal Flask application for testing Passenger deployment
"""
from flask import Flask, render_template_string

# Create minimal Flask app
app = Flask(__name__)

# Simple route that doesn't depend on any other modules
@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minimal Flask App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .success { color: #27ae60; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Minimal Flask Application</h1>
        <p class="success">SUCCESS: Flask is working correctly!</p>
        <p>This is a minimal Flask application that doesn't depend on any project-specific modules.</p>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=False)