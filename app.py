"""
Refactored CV vs Job Description Analyzer - Flask Application
"""
import os
import time
import datetime
import bleach
import httpx
import markdown2
import logging # Use standard logging
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, session, g # Use g for request-local storage
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from langdetect import detect, LangDetectException
from slugify import slugify
from datetime import timezone
from werkzeug.middleware.proxy_fix import ProxyFix

# 1. Configuration and Constants
load_dotenv() # Load environment variables

# Application Configuration
# IMPORTANT: Replace this with a strong, random key. Use environment variables in production.
SECRET_KEY = os.getenv('SECRET_KEY', 'REPLACE_THIS_WITH_A_VERY_STRONG_RANDOM_KEY')
if SECRET_KEY == 'REPLACE_THIS_WITH_A_VERY_STRONG_RANDOM_KEY':
    logging.warning("SECRET_KEY is not set via environment variable. Using default placeholder.")

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS_FOLDER = os.path.join(APP_ROOT, 'reports')
FEEDBACK_FOLDER = os.path.join(APP_ROOT, 'feedback')
SESSION_FOLDER = os.path.join(APP_ROOT, 'flask_session') # For filesystem sessions if needed

# Ensure directories exist
os.makedirs(REPORTS_FOLDER, exist_ok=True)
os.makedirs(FEEDBACK_FOLDER, exist_ok=True)
os.makedirs(SESSION_FOLDER, exist_ok=True)

# File Size Limits (in bytes)
MAX_CONTENT_SIZE_KB = int(os.getenv('MAX_CONTENT_SIZE_KB', 30))
MAX_CONTENT_LENGTH_BYTES = MAX_CONTENT_SIZE_KB * 1024

# Report Retention
REPORT_RETENTION_DAYS = int(os.getenv('REPORT_RETENTION_DAYS', 30))

# LLM API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', 'REPLACE_WITH_YOUR_OPENROUTER_KEY_OR_REMOVE')
# IMPORTANT: Remove or replace the hardcoded API key above if this is committed publicly.
if OPENROUTER_API_KEY == 'REPLACE_WITH_YOUR_OPENROUTER_KEY_OR_REMOVE':
     logging.warning("OPENROUTER_API_KEY is not set via environment variable. Using default placeholder.")

DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek/deepseek-chat-v3-0324')


# Supported Languages and Prompts
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'fr': 'Français'
}

# Import prompts (assuming these files exist and define the templates)
try:
    from prompts.prompts_en import FULL_ANALYSIS_PROMPT_TEMPLATE_EN, CV_REWRITE_PROMPT_TEMPLATE_EN
    from prompts.prompts_fr import FULL_ANALYSIS_PROMPT_TEMPLATE_FR, CV_REWRITE_PROMPT_TEMPLATE_FR

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
except ImportError as e:
    logging.critical(f"Error loading prompt templates: {e}. Ensure prompts/prompts_en.py and prompts/prompts_fr.py exist.")
    PROMPT_TEMPLATES = {} # Define empty to prevent errors later

# Import default values (assuming config.py exists and defines these)
try:
    from config import default_cv, default_jd
except ImportError as e:
    logging.critical(f"Error loading default values from config.py: {e}. Ensure config.py exists.")
    default_cv = "Paste your CV here..."
    default_jd = "Paste the Job Description here..."

# Set debug logging level
logging.getLogger().setLevel(logging.DEBUG)
logging.debug("Debug logging enabled")

# Bleach Allowed Tags (for sanitizing HTML output)
ALLOWED_HTML_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'ul', 'ol', 'li',
    'strong', 'em', 'a', 'code', 'pre', 'blockquote', 'table', 'thead',
    'tbody', 'tr', 'th', 'td', 'hr', 'div', 'span' # Added div/span for potentially structured markdown output
]
ALLOWED_HTML_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'div': ['class'], # Allow classes on div if needed for styling markdown output
    'span': ['class']
}


# Initialize Flask application
app = Flask(__name__)
# Add this line to handle reverse proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

# Apply Configuration
app.config['SECRET_KEY'] = SECRET_KEY
# Set to True in production with HTTPS
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Recommended for modern browsers
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 # Session lifetime in seconds
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH_BYTES
app.config['REPORTS_FOLDER'] = REPORTS_FOLDER
app.config['FEEDBACK_FOLDER'] = FEEDBACK_FOLDER
app.config['APPLICATION_ROOT'] = os.getenv('APPLICATION_ROOT', '/appopvibe')
app.config['SESSION_COOKIE_PATH'] = os.getenv('APPLICATION_ROOT', '/appopvibe')

# Session type config - enable filesystem sessions for better reliability
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = SESSION_FOLDER

# Security Configurations - CSRF disabled due to session issues
# csrf = CSRFProtect(app) # Commented out to disable CSRF
app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF completely

# Setup rate limiting (temporarily disabled)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "1000 per hour"], # Greatly increased limits
    storage_uri="memory://", # Consider more persistent storage like Redis in production
    # Change 'on_breach_notify' to 'on_breach'
    on_breach=lambda limit: logging.warning(f"Rate limit breached for {limit.key}: {limit.limit}"),
    application_limits=["1000 per hour"] # Greatly increased limits
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# 2. Forms Definition
class CVAnalysisForm(FlaskForm):
    """Form for submitting CV and Job Description."""
    cv = TextAreaField('CV', validators=[
        DataRequired('CV is required.'),
        Length(min=100, max=MAX_CONTENT_LENGTH_BYTES,
               message=f'CV must be between 100 characters and {MAX_CONTENT_SIZE_KB}KB in size.')
    ])
    jd = TextAreaField('Job Description', validators=[
        DataRequired('Job Description is required.'),
        Length(min=50, max=MAX_CONTENT_LENGTH_BYTES,
               message=f'Job description must be between 50 characters and {MAX_CONTENT_SIZE_KB}KB in size.')
    ])
    language = SelectField('Language', choices=list(SUPPORTED_LANGUAGES.items()))
    rewrite_cv = BooleanField('Rewrite my CV')


class FeedbackForm(FlaskForm):
    """Form for submitting user feedback."""
    email = StringField('Your Email (Optional)', validators=[Optional()])  # Removed Email validator to avoid dependency
    comments = TextAreaField('Comments', validators=[
        DataRequired('Comments are required.'),
        Length(min=10, message='Comments must be at least 10 characters long.')
    ])


# 3. Helper Functions and Service Logic

def call_llm_api(prompt, temperature=0.7):
    """Calls the OpenRouter API with a given prompt."""
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == 'REPLACE_WITH_YOUR_OPENROUTER_KEY_OR_REMOVE':
        logging.error("OpenRouter API key not configured.")
        return "Error: API key not configured. Please set up your OPENROUTER_API_KEY environment variable."
    
    # Debug API key (truncated for security)
    api_key_preview = OPENROUTER_API_KEY[:6] + "..." + OPENROUTER_API_KEY[-4:] if len(OPENROUTER_API_KEY) > 10 else "too short"
    logging.debug(f"Using API key: {api_key_preview}")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Use X-Title for identification on OpenRouter dashboard
        "X-Title": "CV Analyzer",
         # Required if API key is linked to a specific site
        "HTTP-Referer": os.getenv('OPENROUTER_REFERER', 'https://rametric.com'),
    }
    
    # Debug headers
    logging.debug(f"Request headers: Authorization: Bearer {api_key_preview}, Content-Type: application/json")

    # LLM Model
    model = DEFAULT_MODEL

    # Truncate prompt if necessary (LLM APIs have token limits)
    # Note: This is a crude truncation. A proper tokenization approach is better.
    max_prompt_length = 3800 # Characters is a proxy for tokens
    truncated_prompt = prompt[:max_prompt_length]
    if len(prompt) > max_prompt_length:
        logging.warning(f"Prompt truncated from {len(prompt)} to {max_prompt_length} characters.")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": truncated_prompt}],
        "temperature": temperature,
        "stream": False # Sync call for simplicity in this example
    }

    logging.debug(f"Calling LLM API with model: {model}")

    try:
        # Increased timeout as LLM calls can be slow (120 seconds instead of 60)
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status() # Raise HTTPStatusError for bad responses (4xx or 5xx)
            result = response.json()

            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                logging.info("LLM API call successful.")
                return content
            else:
                logging.error(f"LLM API response missing 'choices': {result}")
                return "Error: Invalid response format from API."

    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP status error from LLM API: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg, exc_info=True)
        
        # Attempt to return API error message if available
        try:
            error_json = e.response.json()
            if 'error' in error_json and 'message' in error_json['error']:
                 error_msg += f" Details: {error_json['error']['message']}"
        except:
            pass # Ignore JSON parsing errors on response text

        return f"Error: {error_msg}"
    except httpx.RequestError as e:
        error_msg = f"HTTP request error occurred during LLM API call: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"An unexpected error occurred during LLM API call: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return f"Error: {error_msg}"

def analyze_cv_jd(cv_text, jd_text, language):
    """Generates analysis using LLM API."""
    logging.debug(f"Starting CV analysis for language: {language}")
    
    if language not in PROMPT_TEMPLATES or 'analysis' not in PROMPT_TEMPLATES[language]:
         logging.error(f"Analysis prompt template missing for language: {language}")
         return "Error: Configuration error for analysis prompt."

    analysis_template = PROMPT_TEMPLATES[language]['analysis']
    analysis_prompt = analysis_template.format(cv=cv_text, jd=jd_text)
    logging.debug(f"Analysis prompt prepared, length: {len(analysis_prompt)}")
    
    result = call_llm_api(analysis_prompt)
    logging.debug(f"Analysis completed, result length: {len(result) if result else 0}")
    return result

def rewrite_cv(cv_text, jd_text, language):
    """Generates rewritten CV using LLM API."""
    logging.debug(f"Starting CV rewriting for language: {language}")
    
    if language not in PROMPT_TEMPLATES or 'rewrite' not in PROMPT_TEMPLATES[language]:
        logging.error(f"Rewrite prompt template missing for language: {language}")
        return "Error: Configuration error for rewrite prompt."

    rewrite_template = PROMPT_TEMPLATES[language]['rewrite']
    rewrite_prompt = rewrite_template.format(cv=cv_text, jd=jd_text)
    logging.debug(f"Rewrite prompt prepared, length: {len(rewrite_prompt)}")
    
    result = call_llm_api(rewrite_prompt)
    logging.debug(f"CV rewrite completed, result length: {len(result) if result else 0}")
    return result

def sanitize_html_output(html_text):
    """Sanitizes HTML content to prevent XSS attacks."""
    if not html_text:
        return ""
    return bleach.clean(
        html_text,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True # Remove tags not in the allow list
    )

def convert_markdown_to_sanitized_html(markdown_text):
    """Converts markdown to HTML and then sanitizes it."""
    if not markdown_text:
        return ""
    try:
        html_output = markdown2.markdown(markdown_text, extras=["tables", "fenced-code-blocks", "nofollow"])
        return sanitize_html_output(html_output)
    except Exception as e:
        logging.error(f"Error converting markdown or sanitizing: {str(e)}", exc_info=True)
        return f"<p>Error displaying content. Raw text:</p><pre>{bleach.clean(markdown_text, tags=[], attributes={}, strip=True)}</pre>"


def generate_report_filename():
    """Generates a unique filename for a report."""
    timestamp = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    return f"report_{timestamp}.md"


def save_report(cv_text, jd_text, analysis_text, rewritten_cv=None, language="English"):
    """Saves the analysis report to a markdown file."""
    filename = generate_report_filename()
    filepath = os.path.join(REPORTS_FOLDER, filename)

    report_content = f"""# CV Analysis Report — {datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ UTC')}

## Language
{language}

## Candidate CV
{cv_text}

## Job Description
{jd_text}


## LLM Analysis
{analysis_text}
"""

    if rewritten_cv:
        report_content += f"""

## Rewritten CV
{rewritten_cv}

"""

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logging.info(f"Report saved successfully: {filename}")
        return filename
    except Exception as e:
        logging.error(f"Error saving report {filename}: {str(e)}", exc_info=True)
        return None # Indicate failure

def save_feedback(email, comments):
    """Saves user feedback to a markdown file."""
    timestamp = datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')
    email_slug = slugify(email or 'anonymous') # Slugify email for filename
    filename = f"feedback_{timestamp}_{email_slug}.md"
    filepath = os.path.join(FEEDBACK_FOLDER, filename)

    feedback_content = f"""# Feedback Received

**Timestamp:** {datetime.datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ UTC')}
**From:** {email or 'Anonymous'}

## Comments
{comments}
"""

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(feedback_content)
        logging.info(f"Feedback saved successfully: {filename}")
        return True
    except Exception as e:
        logging.error(f"Error saving feedback {filename}: {str(e)}", exc_info=True)
        return False # Indicate failure


def clean_old_reports():
    """Deletes reports older than REPORT_RETENTION_DAYS."""
    current_time = time.time()
    max_age_seconds = REPORT_RETENTION_DAYS * 24 * 60 * 60

    cleaned_count = 0
    try:
        for filename in os.listdir(REPORTS_FOLDER):
            filepath = os.path.join(REPORTS_FOLDER, filename)
            if os.path.isfile(filepath) and filename.startswith('report_') and filename.endswith('.md'):
                try:
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logging.info(f"Deleted old report: {filename}")
                        cleaned_count += 1
                except Exception as e:
                    logging.error(f"Failed to delete {filename}: {str(e)}")
        if cleaned_count > 0:
             logging.info(f"Finished cleaning old reports. Deleted {cleaned_count}.")

    except Exception as e:
        logging.error(f"Error during report cleanup process: {str(e)}")

# Simple periodic cleanup check (could be a background task)
# Run cleanup on app startup or periodically.
# For simplicity, we can add a check in a request handler, but a background task is better.
# Let's add a check in the submit route, but with a timestamp debounce.
LAST_CLEANUP_TIME = 0

def run_periodic_cleanup():
    """Runs cleanup if a certain interval has passed."""
    global LAST_CLEANUP_TIME
    current_time = time.time()
    # Run cleanup if it hasn't run in the last hour (3600 seconds)
    CLEANUP_INTERVAL_SECONDS = 3600
    if current_time - LAST_CLEANUP_TIME > CLEANUP_INTERVAL_SECONDS:
        logging.info("Initiating periodic report cleanup.")
        clean_old_reports()
        LAST_CLEANUP_TIME = current_time


def auto_detect_language(text):
    """Attempt to detect the language of the provided text."""
    try:
        lang_code = detect(text)
        # Return 'fr' if detected as fr, otherwise default to 'en'
        return 'fr' if lang_code == 'fr' else 'en'
    except LangDetectException:
        logging.warning("Language detection failed, defaulting to English.")
        return 'en' # Default to English on detection failure


# 4. Routes Definition

@app.route('/', methods=['GET'])
def index():
    """Render the landing page."""
    form = FeedbackForm() # Form for the feedback modal
    
    # Check if redirected from successful feedback submission
    show_success = request.args.get('feedback_success') == 'true'
    
    return render_template('landing.html', 
                          feedback_form=form,
                          show_success_message=show_success) # Pass success flag

@app.route('/form', methods=['GET'])
def form():
    """Render the CV analysis form."""
    try:
        logging.debug("Form route accessed")
        # Check if templates directory exists
        template_path = os.path.join(APP_ROOT, 'templates', 'form.html')
        logging.debug(f"Looking for template at: {template_path}")
        if os.path.exists(template_path):
            logging.debug("form.html template exists")
        else:
            logging.error(f"form.html template NOT FOUND at: {template_path}")
            
        # Create form with try/except around each step
        try:
            form = CVAnalysisForm()
            logging.debug("Created form instance successfully")
        except Exception as form_error:
            logging.error(f"Failed to create form instance: {str(form_error)}", exc_info=True)
            return "Form initialization error. Check logs for details.", 500
        
        # Pre-fill the form with default values if fields are empty
        try:
            if not form.cv.data:
                form.cv.data = default_cv
                logging.debug("Set default CV text")
                
            if not form.jd.data:
                form.jd.data = default_jd
                logging.debug("Set default JD text")
        except Exception as prefill_error:
            logging.error(f"Error pre-filling form: {str(prefill_error)}", exc_info=True)
            # Continue despite this error
            
        # Set default language
        form.language.data = 'en'  # Default to English 
        logging.debug("Form prepared successfully")
        
        # Render with detailed logging
        try:
            return render_template('form.html', form=form)
        except Exception as render_error:
            logging.error(f"Template rendering error: {str(render_error)}", exc_info=True)
            return f"Template error: {str(render_error)}", 500
        
    except Exception as e:
        logging.error(f"Error rendering form: {str(e)}", exc_info=True)
        return f"An error occurred while loading the form: {str(e)}", 500

@app.route('/feedback', methods=['GET', 'POST'])
@app.route('/feedback/', methods=['GET', 'POST'])  # Added trailing slash variant to fix 404s
# Rate limiting disabled for debugging
def submit_feedback():
    """Process feedback submission and save to a markdown file."""
    form = FeedbackForm()
    
    # If it's a GET request, just render the feedback form
    if request.method == 'GET':
        return render_template('feedback.html', form=form)
    
    # For POST requests, process the form
    if form.validate_on_submit():
        email = form.email.data
        comments = form.comments.data
        
        logging.debug(f"Processing feedback submission from {email}")

        success = save_feedback(email, comments)
        if success:
            # Set flash message and ensure it's stored in session
            flash("Thank you for your feedback! We have received it.", "success")
            # Force session to update to ensure flash message is saved
            session.modified = True
            logging.info("Feedback form validated and saved successfully")
            return redirect(url_for('index', feedback_success='true'))
        else:
            flash("An error occurred while saving your feedback. Please try again later.", "danger")
            session.modified = True
            logging.error("Failed to save feedback")
            return redirect(url_for('index'))
    else:
        # Flash validation errors automatically by WTForms or manually iterate
        for field, errors in form.errors.items():
             for error in errors:
                  flash(f"Error in field '{form[field].label.text}': {error}", "danger")
                  session.modified = True
        logging.warning(f"Feedback form validation failed: {form.errors}")
        return render_template('feedback.html', form=form)

@app.route('/submit', methods=['POST'])
# Rate limiting disabled for debugging
def submit():
    """Process the submitted CV and JD, generate analysis, and display results."""
    form = CVAnalysisForm()

    if form.validate_on_submit():
        cv_text = form.cv.data
        jd_text = form.jd.data
        language = form.language.data
        rewrite_requested = form.rewrite_cv.data

        logging.info(f"Processing submission (Language: {language}, Rewrite: {rewrite_requested})")

        # Store language choice in session for form pre-filling on next visit (optional)
        # session['last_lang'] = language

        # 3. Generate Analysis
        analysis_result = analyze_cv_jd(cv_text, jd_text, language)

        # Handle critical errors from analysis generation
        if analysis_result is None or analysis_result.startswith("Error:"):
            flash(f"Analysis failed: {analysis_result or 'Unknown error'}", "danger")
            logging.error(f"Analysis generation failed: {analysis_result}")
            # Re-render form with submitted data
            return render_template('form.html', form=form), 500 # Return server error status

        # 4. Generate Rewritten CV (if requested)
        rewritten_cv = None
        if rewrite_requested:
            rewritten_cv = rewrite_cv(cv_text, jd_text, language)
            if rewritten_cv is None or rewritten_cv.startswith("Error:"):
                flash(f"CV rewrite failed: {rewritten_cv or 'Unknown error'}. Analysis is still available.", "warning")
                logging.warning(f"CV rewrite generation failed: {rewritten_cv}")
                rewritten_cv = None # Ensure None if error string is returned


        # 5. Save Report
        language_name = SUPPORTED_LANGUAGES.get(language, "Unknown")
        report_filename = save_report(
            cv_text,
            jd_text,
            analysis_result, # Save raw result
            rewritten_cv,    # Save raw result (can be None if rewrite failed/not requested)
            language_name
        )
        if not report_filename:
             flash("Could not save the report file. Analysis is shown below.", "warning")

        # 6. Prepare HTML Output
        analysis_html = convert_markdown_to_sanitized_html(analysis_result)
        rewritten_cv_html = convert_markdown_to_sanitized_html(rewritten_cv) if rewritten_cv else None


        # 7. Clean Old Reports (Periodically)
        # Run cleanup periodically, not on every single request.
        run_periodic_cleanup()

        # 8. Render Result
        return render_template(
            'result.html',
            analysis_html=analysis_html,
            rewritten_cv_html=rewritten_cv_html,
            report_filename=report_filename,
            report_url=url_for('download_report', filename=report_filename) if report_filename else None
        )

    else:
        # Form validation failed
        logging.warning(f"CV Analysis form validation failed: {form.errors}")
        # Flash messages are automatically handled by WTForms or the template
        # Re-render the form with validation errors displayed
        return render_template('form.html', form=form), 400 # Return bad request status


@app.route('/reports/<filename>')
def download_report(filename):
    """Download a saved report file."""
    # Security check to prevent path traversal
    base_filename = secure_filename(filename)
    if not base_filename.startswith('report_') or not base_filename.endswith('.md'):
        flash("Invalid report filename.", "danger")
        return redirect(url_for('index'))

    filepath = os.path.join(REPORTS_FOLDER, base_filename)

    # Ensure the file exists and is within the reports folder
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
         flash("Report file not found.", "danger")
         return redirect(url_for('index'))

    # Optional: Add a check here if the report is too old to download?

    try:
        return send_from_directory(REPORTS_FOLDER, base_filename, as_attachment=True)
    except FileNotFoundError:
        flash("Report file not found.", "danger")
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error serving report file {base_filename}: {str(e)}", exc_info=True)
        flash("An error occurred while trying to download the report.", "danger")
        return redirect(url_for('index'))


# 5. Error Handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle files that are too large."""
    flash(f"Content too large. Maximum size is {MAX_CONTENT_SIZE_KB} KB.", "danger")
    return redirect(url_for('form')), 413 # Redirect to form page

@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404 # Assuming you have a 404.html template

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors."""
    # Log the error properly
    logging.error(f"Internal Server Error: {error}", exc_info=True)
    flash("An unexpected server error occurred. Please try again later.", "danger")
    # You could render a specific 500.html template if needed
    return render_template('500.html'), 500 # Assuming you have a 500.html template


# Direct, top-level routes for critical paths to avoid routing issues
@app.route('/appopvibe/feedback/', methods=['GET', 'POST'])
@app.route('/appopvibe/feedback', methods=['GET', 'POST'])
def direct_feedback_route():
    """Hard-coded route to ensure feedback works regardless of APPLICATION_ROOT settings"""
    logging.debug(f"Direct feedback route accessed: {request.path}")
    return submit_feedback()

@app.route('/appopvibe/form')
@app.route('/appopvibe/form/')
def direct_form_route():
    """Hard-coded route to ensure form works regardless of APPLICATION_ROOT settings"""
    logging.debug(f"Direct form route accessed: {request.path}")
    return form()

# Optional: Add explicit routes with APPLICATION_ROOT prefix for proxy deployments
app_root = os.getenv('APPLICATION_ROOT', '/')

if app_root and app_root != '/':
    # Explicit feedback route with APPLICATION_ROOT prefix  
    @app.route(f"{app_root}/feedback", methods=['GET', 'POST'])
    def feedback_with_prefix():
        return submit_feedback()
    
    @app.route(f"{app_root}/feedback/", methods=['GET', 'POST'])
    def feedback_with_prefix_slash():
        return submit_feedback()
    
    # Explicitly handle form and submit routes with prefix
    @app.route(f"{app_root}/form")
    def form_with_prefix():
        return form()
    
    @app.route(f"{app_root}/submit", methods=['POST'])
    def submit_with_prefix():
        return submit()
    
    # Add explicit route for report downloads with APPLICATION_ROOT prefix
    @app.route(f"{app_root}/reports/<filename>")
    def download_report_with_prefix(filename):
        return download_report(filename)

# Entry point for running the app
if __name__ == '__main__':
    # In production, use a production-ready server like Gunicorn or uWSGI
    # app.run(debug=True, host='0.0.0.0')
    print("Running development server. Use a production server like Gunicorn/uWSGI in production.")
    app.run(debug=os.getenv('FLASK_DEBUG') == '1', host='0.0.0.0', port=int(os.getenv('PORT', 5000)))