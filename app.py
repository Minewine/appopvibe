"""
CV vs Job Description Analyzer - Flask Application
"""
import os
import time
import datetime
import bleach
import httpx
import markdown2
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, send_from_directory, session
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from langdetect import detect, LangDetectException
from slugify import slugify
from datetime import timezone

# Load environment variables from .env file
load_dotenv()

# Import prompts
from prompts.prompts_en import FULL_ANALYSIS_PROMPT_TEMPLATE_EN, CV_REWRITE_PROMPT_TEMPLATE_EN
from prompts.prompts_fr import FULL_ANALYSIS_PROMPT_TEMPLATE_FR, CV_REWRITE_PROMPT_TEMPLATE_FR

# Import default values from config.py
from config import default_cv, default_jd

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_SIZE_KB', 30)) * 1024
app.config['REPORTS_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

# Ensure the reports directory exists
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

# Ensure the feedback directory exists
app.config['FEEDBACK_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feedback')
os.makedirs(app.config['FEEDBACK_FOLDER'], exist_ok=True)

# Setup CSRF protection
csrf = CSRFProtect(app)

# Setup rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "20 per hour"],
    storage_uri="memory://",
)

# Constants
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'fr': 'Français'
}

PROMPT_TEMPLATES = {
    'en': {
        'analysis': FULL_ANALYSIS_PROMPT_TEMPLATE_EN,
        'rewrite': CV_REWRITE_PROMPT_TEMPLATE_EN
    },
    'fr': {
        'analysis': FULL_ANALYSIS_PROMPT_TEMPLATE_FR,
        'rewrite': CV_REWRITE_PROMPT_TEMPLATE_FR
    }
}

# Form definition
class CVAnalysisForm(FlaskForm):
    cv = TextAreaField('CV', validators=[
        DataRequired(),
        Length(min=100, max=int(os.getenv('MAX_CONTENT_SIZE_KB', 30)) * 1024, 
               message='CV must be between 100 characters and 30KB in size')
    ])
    jd = TextAreaField('Job Description', validators=[
        DataRequired(),
        Length(min=50, max=int(os.getenv('MAX_CONTENT_SIZE_KB', 30)) * 1024,
               message='Job description must be between 50 characters and 30KB in size')
    ])
    language = SelectField('Language', choices=[('en', 'English'), ('fr', 'Français')])
    rewrite_cv = BooleanField('Rewrite my CV')

def auto_detect_language(text):
    """Attempt to detect the language of the provided text"""
    try:
        lang_code = detect(text)
        return 'fr' if lang_code == 'fr' else 'en'  # Default to English for anything but French
    except LangDetectException:
        return 'en'  # Default to English on detection failure

def call_openrouter_api(prompt, temperature=0.7):
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OpenRouter API key not found.")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    model = 'openai/gpt-3.5-turbo:free'  # Try a different default model

    # Further reduce the prompt size to avoid excessive payload size
    max_length = 3800  # Slightly reduce max_length further
    truncated_prompt = prompt[:max_length]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": truncated_prompt}],
        "temperature": temperature,
        "stream": False
    }

    app.logger.debug(f"Sending payload to OpenRouter: {payload}")
    app.logger.debug(f"Headers: {headers}")

    try:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(url, json=payload, headers=headers)
            # Log detailed error response from API
            if response.status_code != 200:
                app.logger.error(f"OpenRouter API Error {response.status_code}: {response.text}")
            response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)
            result = response.json()
            # Check if 'choices' exists and is not empty
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content']
            else:
                app.logger.error(f"OpenRouter API response missing 'choices': {result}")
                return "Error: Invalid response format from API."
    except httpx.HTTPStatusError as e: # Catch status errors specifically
        error_msg = f"HTTP status error occurred: {e.response.status_code} - {e.response.text}"
        app.logger.error(error_msg)
        return f"Error: {error_msg}"
    except httpx.RequestError as e: # Catch request errors (network, timeout, etc.)
        error_msg = f"HTTP request error occurred: {str(e)}"
        app.logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        app.logger.error(error_msg)
        return f"Error: {error_msg}"

def sanitize_markdown(markdown_text):
    """Sanitize markdown content to prevent XSS attacks"""
    return bleach.clean(
        markdown_text,
        tags=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'ul', 'ol', 'li', 
              'strong', 'em', 'a', 'code', 'pre', 'blockquote', 'table', 'thead', 
              'tbody', 'tr', 'th', 'td', 'hr'],
        attributes={'a': ['href', 'title', 'target']}
    )

def generate_report_filename(language="en"):
    timestamp = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    return f"report_{timestamp}.md"


def save_report(cv_text, jd_text, analysis_text, rewritten_cv=None, language="English"):
    timestamp = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    report_content = f"""# CV Analysis Report — {timestamp}

## Language
{language}

## Candidate CV
```
{cv_text}
```

## Job Description
```
{jd_text}
```

## LLM Analysis
{analysis_text}
"""

    if rewritten_cv:
        report_content += f"""

## Rewritten CV
```
{rewritten_cv}
```
"""

    filename = generate_report_filename()
    filepath = os.path.join(app.config['REPORTS_FOLDER'], filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return filename

def clean_old_reports():
    """Delete reports older than REPORT_RETENTION_DAYS"""
    retention_days = int(os.getenv('REPORT_RETENTION_DAYS', 30))
    current_time = time.time()
    max_age = retention_days * 24 * 60 * 60
    
    for filename in os.listdir(app.config['REPORTS_FOLDER']):
        if filename.startswith('report_') and filename.endswith('.md'):
            filepath = os.path.join(app.config['REPORTS_FOLDER'], filename)
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age:
                try:
                    os.remove(filepath)
                    app.logger.info(f"Deleted old report: {filename}")
                except Exception as e:
                    app.logger.error(f"Failed to delete {filename}: {str(e)}")

@app.route('/', methods=['GET'])
def index():
    """Render the landing page"""
    form = FlaskForm()  # Just for CSRF token in the feedback form
    return render_template('landing.html', form=form)

@app.route('/form', methods=['GET'])
def form():
    """Render the CV analysis form"""
    form = CVAnalysisForm()
    # Pre-fill the form with default values if fields are empty
    form.cv.data = default_cv
    form.jd.data = default_jd
    return render_template('form.html', form=form)

@app.route('/feedback', methods=['POST'])
@limiter.limit("10 per day")
def submit_feedback():
    """Process feedback submission and save to a markdown file."""
    email = request.form.get('email', '')
    comments = request.form.get('comments', '')

    if not email or not comments:
        flash("Veuillez remplir tous les champs requis.", "danger")
        return redirect(url_for('index'))

    try:
        # Generate filename
        timestamp = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
        # Slugify email for filename, handle potential empty email or invalid chars
        email_slug = slugify(email) if email else 'anonymous'
        filename = f"feedback_{timestamp}_{email_slug}.md"
        filepath = os.path.join(app.config['FEEDBACK_FOLDER'], filename)

        # Format content
        feedback_content = f"""# Feedback Received

**Timestamp:** {timestamp}
**From:** {email}

## Comments

```
{comments}
```
"""

        # Save the feedback to a file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(feedback_content)

        app.logger.info(f"Feedback received from {email} and saved to {filename}")

        flash("Merci pour vos commentaires! Nous les avons bien reçus.", "success") # Updated flash message
    except Exception as e:
        app.logger.error(f"Error processing or saving feedback: {str(e)}", exc_info=True) # Add exc_info for more details
        flash("Une erreur s'est produite lors de l'enregistrement de vos commentaires. Veuillez réessayer plus tard.", "danger")

    return redirect(url_for('index'))

def _validate_form(form):
    """Validate the CVAnalysisForm and flash errors if invalid."""
    if not form.validate_on_submit():
        app.logger.warning(f"Form validation failed: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Erreur dans le champ '{form[field].label.text}': {error}", "danger")
        return False
    return True

def _extract_form_data(form):
    """Extract data from the validated CVAnalysisForm."""
    cv_text = form.cv.data
    jd_text = form.jd.data
    language = form.language.data
    rewrite_requested = form.rewrite_cv.data
    app.logger.info(f"Processing submission: lang={language}, rewrite={rewrite_requested}")
    return cv_text, jd_text, language, rewrite_requested

def _generate_analysis(cv_text, jd_text, language):
    """Generate analysis using the OpenRouter API."""
    try:
        analysis_template = PROMPT_TEMPLATES[language]['analysis']
        analysis_prompt = analysis_template.format(cv=cv_text, jd=jd_text)
        analysis_result = call_openrouter_api(analysis_prompt)
        if analysis_result.startswith("Error:"):
            flash(f"Erreur lors de la génération de l'analyse: {analysis_result}", "danger")
            return None # Indicate error
        return analysis_result
    except KeyError:
        app.logger.error(f"Invalid language code '{language}' used for analysis prompt template.")
        flash("Erreur interne du serveur: Configuration de langue invalide.", "danger")
        return None # Indicate error
    except Exception as e:
        app.logger.error(f"Unexpected error during analysis generation: {str(e)}", exc_info=True)
        flash("Une erreur inattendue s'est produite lors de la génération de l'analyse.", "danger")
        return None # Indicate error

def _generate_rewrite(cv_text, jd_text, language):
    """Generate rewritten CV using the OpenRouter API."""
    try:
        rewrite_template = PROMPT_TEMPLATES[language]['rewrite']
        rewrite_prompt = rewrite_template.format(cv=cv_text, jd=jd_text)
        rewritten_cv = call_openrouter_api(rewrite_prompt)
        if rewritten_cv.startswith("Error:"):
            flash(f"Erreur lors de la réécriture du CV: {rewritten_cv}", "warning")
            return None # Indicate error but allow analysis to proceed
        return rewritten_cv
    except KeyError:
        app.logger.error(f"Invalid language code '{language}' used for rewrite prompt template.")
        flash("Erreur interne du serveur: Configuration de langue invalide pour la réécriture.", "warning")
        return None # Indicate error
    except Exception as e:
        app.logger.error(f"Unexpected error during CV rewrite: {str(e)}", exc_info=True)
        flash("Une erreur inattendue s'est produite lors de la réécriture du CV.", "warning")
        return None # Indicate error

def _prepare_html_output(analysis_result, rewritten_cv):
    """Convert markdown results to sanitized HTML."""
    analysis_html = None
    rewritten_cv_html = None
    try:
        if analysis_result:
            analysis_html = markdown2.markdown(analysis_result, extras=["tables", "fenced-code-blocks", "nofollow"])
            analysis_html = sanitize_markdown(analysis_html)

        if rewritten_cv:
            rewritten_cv_html = markdown2.markdown(rewritten_cv, extras=["tables", "fenced-code-blocks", "nofollow"])
            rewritten_cv_html = sanitize_markdown(rewritten_cv_html)
    except Exception as e:
        app.logger.error(f"Error converting markdown to HTML or sanitizing: {str(e)}", exc_info=True)
        flash("Erreur lors de l'affichage des résultats. Veuillez vérifier le rapport téléchargé.", "danger")
        # Fallback: display raw text or error message if conversion fails
        if analysis_result and not analysis_html:
             analysis_html = f"<p>Error displaying analysis. Please download the report.</p><pre>{bleach.clean(analysis_result)}</pre>" # Sanitize raw text too
        if rewritten_cv and not rewritten_cv_html:
             rewritten_cv_html = f"<p>Error displaying rewritten CV.</p><pre>{bleach.clean(rewritten_cv)}</pre>" # Sanitize raw text too

    return analysis_html, rewritten_cv_html

@app.route('/submit', methods=['POST'])
@limiter.limit("5 per hour")
def submit():
    """Process the submitted CV and JD, generate analysis, and display results."""
    form = CVAnalysisForm()

    # 1. Validate Form
    if not _validate_form(form):
        return render_template('form.html', form=form), 400

    # 2. Extract Data
    cv_text, jd_text, language, rewrite_requested = _extract_form_data(form)

    # 3. Generate Analysis
    analysis_result = _generate_analysis(cv_text, jd_text, language)
    if analysis_result is None: # Check if analysis generation failed critically
        return redirect(url_for('form'))

    # 4. Generate Rewritten CV (if requested)
    rewritten_cv = None
    if rewrite_requested:
        rewritten_cv = _generate_rewrite(cv_text, jd_text, language)
        # Note: We proceed even if rewrite fails, as analysis might be useful.

    # 5. Save Report
    language_name = SUPPORTED_LANGUAGES.get(language, "Unknown")
    report_filename = save_report(
        cv_text,
        jd_text,
        analysis_result, # Save raw result
        rewritten_cv,    # Save raw result
        language_name
    )
    if not report_filename:
         flash("Impossible d'enregistrer le rapport. L'analyse est toujours affichée ci-dessous.", "warning")

    # 6. Prepare HTML Output
    analysis_html, rewritten_cv_html = _prepare_html_output(analysis_result, rewritten_cv)

    # 7. Clean Old Reports (Periodically)
    # Consider moving this to a scheduled task (e.g., APScheduler, Celery)
    try:
        # Simple periodic check - adjust frequency as needed
        if datetime.datetime.now().minute % 15 == 0: # Run approx every 15 mins
            clean_old_reports()
    except Exception as e:
        app.logger.error(f"Error during periodic report cleanup: {str(e)}", exc_info=True)

    # 8. Render Result
    return render_template(
        'result.html',
        analysis_html=analysis_html,
        rewritten_cv_html=rewritten_cv_html,
        report_filename=report_filename
    )

@app.route('/reports/<filename>')
def download_report(filename):
    """Download a saved report file"""
    # Security check to prevent path traversal
    filename = secure_filename(filename)
    if not filename.startswith('report_') or not filename.endswith('.md'):
        flash("Invalid report filename", "danger")
        return redirect(url_for('index'))
        
    return send_from_directory(app.config['REPORTS_FOLDER'], filename, as_attachment=True)

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle files that are too large"""
    flash(f"Content too large. Maximum size is {os.getenv('MAX_CONTENT_SIZE_KB', 30)} KB", "danger")
    return redirect(url_for('index')), 413

# Run the app if executed directly
if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            host='0.0.0.0', 
            port=int(os.getenv('PORT', 5000)))
