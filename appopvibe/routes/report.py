"""
Report routes for the CV Analyzer application.
"""
import os
from flask import (
    Blueprint, render_template, send_from_directory,
    current_app, abort, session
)
from appopvibe.services import ReportService

# Create blueprint
report_bp = Blueprint('report', __name__, url_prefix='/report')

@report_bp.route('/<report_id>')
def view_report(report_id):
    """Display a CV analysis report."""
    # Security check - only allow viewing if report ID matches session
    if 'current_report_id' not in session or session['current_report_id'] != report_id:
        abort(403)
        
    reports_folder = current_app.config.get('REPORTS_FOLDER', 'reports')
    report_service = ReportService(reports_directory=reports_folder)
    report_html = report_service.get_report_html(report_id)
    
    if report_html is None:
        abort(404)
        
    return render_template('report.html', report_content=report_html)

@report_bp.route('/download/<report_id>')
def download_report(report_id):
    """Download the raw report file."""
    # Security check - only allow download if report ID matches session
    if 'current_report_id' not in session or session['current_report_id'] != report_id:
        abort(403)
        
    reports_folder = current_app.config.get('REPORTS_FOLDER', 'reports')
    try:
        return send_from_directory(
            reports_folder,
            f"{report_id}.md",
            as_attachment=True,
            download_name=f"cv_analysis_{report_id}.md"
        )
    except FileNotFoundError:
        abort(404)
