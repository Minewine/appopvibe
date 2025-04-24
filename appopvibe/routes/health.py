"""
Health check routes for the CV Analyzer application.
"""
import os
import sys
import platform
import logging
from flask import Blueprint, jsonify, current_app

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/health')

# Setup logger
logger = logging.getLogger(__name__)

@health_bp.route('/', methods=['GET'])
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'cv-analyzer',
    }), 200

@health_bp.route('/detailed', methods=['GET'])
def detailed_health():
    """Detailed health check with system information."""
    # Check access to key directories
    templates_ok = os.path.exists(current_app.template_folder)
    static_ok = os.path.exists(current_app.static_folder)
    
    # Basic system information
    system_info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'templates_accessible': templates_ok,
        'static_files_accessible': static_ok,
    }
    
    health_status = {
        'status': 'ok' if (templates_ok and static_ok) else 'degraded',
        'service': 'cv-analyzer',
        'system_info': system_info,
    }
    
    return jsonify(health_status), 200 if health_status['status'] == 'ok' else 503
