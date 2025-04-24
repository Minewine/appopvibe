"""
Application factory for the CV Analyzer application.
"""
import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from appopvibe.config import DevelopmentConfig, ProductionConfig, TestingConfig

# Initialize extensions
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

def create_app(config_class=None):
    """Create and configure the Flask application."""
    # Create Flask app with correct template and static folder paths
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Determine configuration
    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            config_class = ProductionConfig
        elif env == 'testing':
            config_class = TestingConfig
        else:
            config_class = DevelopmentConfig
    
    app.config.from_object(config_class)
    
    # Initialize extensions
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    from appopvibe.routes.main import main_bp
    from appopvibe.routes.report import report_bp
    from appopvibe.routes.feedback import feedback_bp
    from appopvibe.routes.health import health_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(health_bp)
    
    # Print startup message
    port = app.config.get('PORT', 5000)
    print(f" * Running on http://127.0.0.1:{port}")
    print(f" * Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f" * Template directory: {template_dir}")
    
    return app
