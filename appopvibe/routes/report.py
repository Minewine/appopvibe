"""
Report routes for the CV Analyzer application.
"""
import os
import re
from flask import (
    Blueprint, render_template, send_from_directory,
    current_app, abort, session
)
from appopvibe.services import ReportService

report_bp = Blueprint('report', __name__, url_prefix='/report')
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


def _checked_id(report_id: str) -> str:
    if not _ID_RE.match(report_id or ""):
        abort(404)
    if session.get('current_report_id') != report_id:
        abort(403)
    return report_id


@report_bp.route('/<report_id>')
def view_report(report_id):
    """Display a CV analysis report."""
    report_id = _checked_id(report_id)
    reports_folder = current_app.config.get('REPORTS_FOLDER', 'reports')
    report_service = ReportService(reports_directory=reports_folder)
    report_html = report_service.get_report_html(report_id)
    if report_html is None:
        abort(404)
    return render_template('report.html', report_content=report_html, report_id=report_id)


@report_bp.route('/download/<report_id>')
def download_report(report_id):
    """Download the raw report file."""
    report_id = _checked_id(report_id)
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
