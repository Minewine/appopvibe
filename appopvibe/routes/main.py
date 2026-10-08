"""
Main routes for the CV Analyzer application.
"""
import asyncio
import logging
import os

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, session
)

from appopvibe import limiter
from appopvibe.models import CVAnalysisForm
from appopvibe.services import AnalyzerService, ReportService, LLMService

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

MAX_FIELD_CHARS = 12000


def _prompts_for(language: str) -> dict:
    if language == 'fr':
        from prompts.prompts_fr import (
            SYSTEM_FR, ANALYSIS_USER_FR, REWRITE_SYSTEM_FR, REWRITE_USER_FR
        )
        return {
            'system': SYSTEM_FR,
            'analysis': ANALYSIS_USER_FR,
            'rewrite_system': REWRITE_SYSTEM_FR,
            'rewrite': REWRITE_USER_FR,
        }
    from prompts.prompts_en import (
        SYSTEM_EN, ANALYSIS_USER_EN, REWRITE_SYSTEM_EN, REWRITE_USER_EN
    )
    return {
        'system': SYSTEM_EN,
        'analysis': ANALYSIS_USER_EN,
        'rewrite_system': REWRITE_SYSTEM_EN,
        'rewrite': REWRITE_USER_EN,
    }


@main_bp.route('/', methods=['GET'])
def index():
    """Render the landing page."""
    return render_template('landing.html')


@main_bp.route('/form', methods=['GET'])
def submit_cv():
    """Render an empty CV analysis form. Do not prefill personal data."""
    return render_template('form.html', form=CVAnalysisForm())


@main_bp.route('/analyze', methods=['POST'])
@limiter.limit("5 per minute")
def analyze():
    """Process the CV and job description for analysis."""
    form = CVAnalysisForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "error")
        return render_template('form.html', form=form), 400

    cv_text = (form.cv.data or '').strip()
    jd_text = (form.jd.data or '').strip()
    if len(cv_text) > MAX_FIELD_CHARS or len(jd_text) > MAX_FIELD_CHARS:
        flash(f"CV and job description must each be under {MAX_FIELD_CHARS} characters.", "error")
        return render_template('form.html', form=form), 400

    language = form.language.data or 'en'
    rewrite_cv = bool(form.rewrite_cv.data)

    try:
        logger.info("Processing submission - Language: %s, Rewrite CV: %s", language, rewrite_cv)
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            logger.error("No GROQ_API_KEY found in environment variables")
            raise ValueError("Missing GROQ_API_KEY environment variable")

        model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
        llm_service = LLMService(api_key=groq_api_key, provider="groq", default_model=model)
        logger.info("Using %s with model %s", llm_service.provider, llm_service.default_model)

        analyzer_service = AnalyzerService(llm_service, _prompts_for(language))
        result = asyncio.run(
            analyzer_service.process_submission(cv_text, jd_text, language, rewrite_cv)
        )

        reports_dir = current_app.config.get('REPORTS_FOLDER', os.path.join(os.getcwd(), 'reports'))
        os.makedirs(reports_dir, exist_ok=True)
        report_service = ReportService(reports_directory=reports_dir)
        report_id = report_service.save_report(
            cv_text,
            jd_text,
            result.get('analysis', ''),
            result.get('rewritten_cv'),
            language,
        )
        session['current_report_id'] = report_id
        return redirect(url_for('report.view_report', report_id=report_id))

    except Exception as e:
        logger.exception("Error processing submission: %s", e)
        flash("An error occurred while analyzing your CV. Please try again.", "error")
        return render_template('form.html', form=form), 500


@main_bp.route('/feedback', methods=['GET', 'POST'])
@main_bp.route('/feedback/', methods=['GET', 'POST'])
def feedback():
    """Handle feedback form submission."""
    if request.method == 'POST':
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('main.index'))
    return redirect(url_for('main.index') + '#feedback')
