"""
Report routes for the CV Analyzer application.
"""
import os
import re
from io import BytesIO

from flask import (
    Blueprint, render_template, send_from_directory, send_file,
    current_app, abort, session, flash, redirect, url_for
)
from appopvibe.services import ReportService
from appopvibe.services.report.swiss_cv import build_swiss_cv, extract_cv_for_docx

report_bp = Blueprint("report", __name__, url_prefix="/report")
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


def _checked_id(report_id: str) -> str:
    if not _ID_RE.match(report_id or ""):
        abort(404)
    if session.get("current_report_id") != report_id:
        abort(403)
    return report_id


@report_bp.route("/<report_id>")
def view_report(report_id):
    """Display a CV analysis report."""
    report_id = _checked_id(report_id)
    reports_folder = current_app.config.get("REPORTS_FOLDER", "reports")
    report_service = ReportService(reports_directory=reports_folder)
    report_html = report_service.get_report_html(report_id)
    if report_html is None:
        abort(404)
    markdown = report_service.get_report(report_id) or ""
    cv_markdown, _, source = extract_cv_for_docx(markdown)
    return render_template(
        "report.html",
        report_content=report_html,
        report_id=report_id,
        can_download_docx=bool(cv_markdown),
        docx_source=source,
    )


@report_bp.route("/download/<report_id>")
def download_report(report_id):
    """Download the raw report file."""
    report_id = _checked_id(report_id)
    reports_folder = current_app.config.get("REPORTS_FOLDER", "reports")
    try:
        return send_from_directory(
            reports_folder,
            f"{report_id}.md",
            as_attachment=True,
            download_name=f"cv_analysis_{report_id}.md",
        )
    except FileNotFoundError:
        abort(404)


@report_bp.route("/download-docx/<report_id>")
def download_docx(report_id):
    """Download the CV as a Swiss-style Word document."""
    report_id = _checked_id(report_id)
    reports_folder = current_app.config.get("REPORTS_FOLDER", "reports")
    report_service = ReportService(reports_directory=reports_folder)
    markdown = report_service.get_report(report_id)
    if not markdown:
        abort(404)
    cv_markdown, language, source = extract_cv_for_docx(markdown)
    if not cv_markdown:
        flash("No CV text was found in this report.", "error")
        return redirect(url_for("report.view_report", report_id=report_id))
    try:
        payload = build_swiss_cv(cv_markdown, language)
    except RuntimeError as exc:
        flash(str(exc), "error")
        return redirect(url_for("report.view_report", report_id=report_id))
    name = "cv_rewritten" if source == "rewritten" else "cv_original"
    return send_file(
        BytesIO(payload),
        as_attachment=True,
        download_name=f"{name}_{language}_{report_id}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
