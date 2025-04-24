"""
Feedback routes for the CV Analyzer application.
"""
import os
import logging
import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app
)

from appopvibe.models.forms import FeedbackForm

# Create blueprint
feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

# Setup logger
logger = logging.getLogger(__name__)

@feedback_bp.route('/', methods=['GET', 'POST'])
def submit_feedback():
    """Submit user feedback."""
    form = FeedbackForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            # Get form data
            email = form.email.data
            feedback_text = form.feedback.data
            rating = form.rating.data
            
            # Create filename with timestamp and email (if provided)
            timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
            email_slug = "anonymous"
            if email:
                email_slug = email.replace('@', '-').replace('.', '-')
                
            filename = f"feedback_{timestamp}_{email_slug}.md"
            
            # Create feedback content
            feedback_content = f"""# User Feedback

Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
Rating: {rating}/5
Email: {email or 'Not provided'}

## Feedback:

{feedback_text}
"""
            
            # Save feedback to file
            feedback_dir = current_app.config.get('FEEDBACK_FOLDER', 'feedback')
            os.makedirs(feedback_dir, exist_ok=True)
            
            with open(os.path.join(feedback_dir, filename), 'w', encoding='utf-8') as f:
                f.write(feedback_content)
                
            # Show success message
            flash("Thank you for your feedback! We appreciate your input.")
            return redirect(url_for('main.index'))
            
        except Exception as e:
            logger.exception(f"Error saving feedback: {e}")
            flash("An error occurred while submitting feedback. Please try again.")
    
    # Show feedback form
    return render_template('feedback.html', form=form)
