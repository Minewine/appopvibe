"""
Routes package for the CV Analyzer application.
"""
from appopvibe.routes.main import main_bp
from appopvibe.routes.report import report_bp
from appopvibe.routes.feedback import feedback_bp
from appopvibe.routes.health import health_bp

__all__ = ['main_bp', 'report_bp', 'feedback_bp', 'health_bp']
