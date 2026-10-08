"""
Report routes for the CV Analyzer application.
"""
import re
from io import BytesIO

from flask import (
    Blueprint, render_template, send_file, Response,
    current_app, abort
)
from appopvibe.services import ReportService
from appopvibe.services.report.swiss_cv import build_swiss_cv, extract_cv_for_docx

report_bp = Blueprint("report", __name__, url_prefix="/report")
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


def _service():
    reports_folder = current_app.config.get("REPORTS_FOLDER", "reports")
    return ReportService(reports_directory=reports_folder)


def _checked_id(report_id: str) -> str:
    if not _ID_RE.match(report_id or ""):
        abort(404)
    return report_id


@report_bp.route("/download/<report_id>")
def download_report(report_id):
    """Download the saved report markdown."""
    report_id = _checked_id(report_id)
    report_service = _service()
    text = report_service.get_report(report_id)
    if not text:
        abort(404)
    return Response(
        text,
        mimetype="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=cv_analysis_{report_id}.md"},
    )


@report_bp.route("/download-docx/<report_id>")
def download_docx(report_id):
    """Download the CV as a Swiss-style Word document."""
    report_id = _checked_id(report_id)
    report_service = _service()
    markdown = report_service.get_report(report_id)
    if not markdown:
        abort(404)
    cv_markdown, language, source = extract_cv_for_docx(markdown)
    if not cv_markdown:
        cv_markdown = markdown
        source = "report"
    try:
        payload = build_swiss_cv(cv_markdown, language)
    except Exception:
        current_app.logger.exception("DOCX build failed")
        payload = _plain_docx(cv_markdown)
    name = "cv_rewritten" if source == "rewritten" else "cv"
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={name}_{language}_{report_id}.docx"},
    )


def _plain_docx(text: str) -> bytes:
    from docx import Document
    doc = Document()
    for line in (text or "CV").splitlines():
        doc.add_paragraph(line[:500])
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


@report_bp.route("/<report_id>")
def view_report(report_id):
    """Display a CV analysis report."""
    report_id = _checked_id(report_id)
    report_service = _service()
    report_html = report_service.get_report_html(report_id)
    if report_html is None:
        abort(404)
    markdown = report_service.get_report(report_id) or ""
    cv_markdown, _, source = extract_cv_for_docx(markdown)
    return render_template(
        "report.html",
        report_content=report_html,
        report_id=report_id,
        can_download_docx=bool(cv_markdown or markdown),
        docx_source=source,
    )
