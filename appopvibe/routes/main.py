"""
Main routes for the CV Analyzer application.
"""
import os
import logging
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, abort, session
)

from appopvibe.models import CVAnalysisForm
from appopvibe.services import AnalyzerService, ReportService

# Create blueprint
main_bp = Blueprint('main', __name__)

# Setup logger
logger = logging.getLogger(__name__)

@main_bp.route('/', methods=['GET'])
def index():
    """Render the landing page."""
    return render_template('landing.html')

@main_bp.route('/form', methods=['GET'])
def submit_cv():
    """Render the CV analysis form with default values from config."""
    # Import from root config.py file, not from appopvibe.config
    from config import default_cv, default_jd
    
    form = CVAnalysisForm()
    
    # Only pre-populate if form is not already populated
    if not form.cv.data:
        form.cv.data = default_cv
    if not form.jd.data:
        form.jd.data = default_jd
        
    return render_template('form.html', form=form)

@main_bp.route('/analyze', methods=['POST'])
async def analyze():
    """Process the CV and job description for analysis."""
    form = CVAnalysisForm()
    
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {field}: {error}", "error")
        return redirect(url_for('main.index'))
    
    try:
        # Get form data
        cv_text = form.cv.data
        jd_text = form.jd.data
        language = form.language.data
        rewrite_cv = form.rewrite_cv.data
        
        # Log submission
        logger.info(f"Processing submission - Language: {language}, Rewrite CV: {rewrite_cv}")
        
        # Create required services
        from appopvibe.services import LLMService
        from appopvibe.services.llm.llm_service import LLMProvider
        import os
        from flask import current_app
        
        # Define default templates since PROMPT_TEMPLATES is not in config
        DEFAULT_TEMPLATES = {
            'en': {
                'analysis': """Analyze the match between this CV and job description:
                    CV: {cv}
                    
                    JOB DESCRIPTION: {jd}
                    
                    Provide a detailed analysis of how well the candidate's experience, 
                    skills and qualifications match the job requirements. Include:
                    1. Overall match score (as a percentage)
                    2. Key strengths and matches
                    3. Notable gaps and weaknesses
                    4. Specific recommendations to improve the CV
                """,
                'rewrite': """Rewrite this CV to better match the job description:
                    ORIGINAL CV: {cv}
                    
                    JOB DESCRIPTION: {jd}
                    
                    Create an optimized version of the CV that:
                    1. Highlights relevant experience and skills
                    2. Uses keywords from the job description
                    3. Presents achievements with metrics where possible
                    4. Is formatted for ATS compatibility
                """
            },
            'fr': {
                'analysis': """Analysez la correspondance entre ce CV et cette description de poste:
                    CV: {cv}
                    
                    DESCRIPTION DU POSTE: {jd}
                    
                    Fournissez une analyse détaillée de l'adéquation entre l'expérience, 
                    les compétences et les qualifications du candidat et les exigences du poste. Incluez:
                    1. Score de correspondance global (en pourcentage)
                    2. Points forts et correspondances clés
                    3. Lacunes et faiblesses notables
                    4. Recommandations spécifiques pour améliorer le CV
                """,
                'rewrite': """Réécrivez ce CV pour mieux correspondre à la description du poste:
                    CV ORIGINAL: {cv}
                    
                    DESCRIPTION DU POSTE: {jd}
                    
                    Créez une version optimisée du CV qui:
                    1. Met en évidence l'expérience et les compétences pertinentes
                    2. Utilise des mots-clés de la description du poste
                    3. Présente les réalisations avec des métriques si possible
                    4. Est formaté pour la compatibilité ATS
                """
            }
        }
        
        # Set up directories
        reports_dir = current_app.config.get('REPORTS_FOLDER', os.path.join(os.getcwd(), 'reports'))
        os.makedirs(reports_dir, exist_ok=True)
        
        # Initialize services with required dependencies and explicitly set API key
        # Get API keys directly from environment
        groq_api_key = os.getenv('GROQ_API_KEY')
        
        if not groq_api_key:
            logger.error("No GROQ_API_KEY found in environment variables")
            raise ValueError("Missing GROQ_API_KEY environment variable")
            
        # Initialize LLM service with explicit API key and provider
        llm_service = LLMService(
            api_key=groq_api_key,
            provider="groq",
            default_model="llama-3.3-70b-versatile"
        )
        
        logger.info(f"Using {llm_service.provider} as LLM provider with model {llm_service.default_model}")
        
        analyzer_service = AnalyzerService(llm_service, DEFAULT_TEMPLATES)
        report_service = ReportService(reports_directory=reports_dir)
        
        # Analyze CV and job description
        result = await analyzer_service.process_submission(
            cv_text, jd_text, language, rewrite_cv
        )
        
        # Handle both cases: when result is a tuple or a single value
        if isinstance(result, tuple) and len(result) == 2:
            analysis_result, rewrite_result = result
        else:
            # If only one result is returned, assume it's the analysis
            analysis_result = result
            rewrite_result = None
            logger.warning("process_submission returned only one value instead of two")
        
        # Save results to a report file
        report_filename = report_service.save_report(
            cv_text, jd_text, analysis_result, 
            rewrite_result if rewrite_cv else None,
            language
        )
        
        # Save report ID in session for security
        session['current_report_id'] = report_filename
        
        # Redirect to the report view
        return redirect(url_for('report.view_report', report_id=report_filename))
    
    except Exception as e:
        logger.exception(f"Error processing submission: {e}")
        flash("An error occurred while analyzing your CV. Please try again.", "error")
        return redirect(url_for('main.index'))

@main_bp.route('/feedback', methods=['GET', 'POST'])
@main_bp.route('/feedback/', methods=['GET', 'POST'])
def feedback():
    """Handle feedback form submission."""
    if request.method == 'POST':
        # Process the feedback submission (you can add more processing code here)
        flash('Thank you for your feedback!', 'success')
        # Redirect back to the landing page instead of staying on feedback
        return redirect(url_for('main.index'))
    
    # For GET requests, redirect to the landing page with a fragment to scroll to the feedback section
    return redirect(url_for('main.index') + '#feedback')
