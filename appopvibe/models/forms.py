"""
Form models for the CV Analyzer application.
"""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, BooleanField, StringField
from wtforms.validators import DataRequired, Email, Optional, Length

class CVAnalysisForm(FlaskForm):
    """Form for CV vs Job Description analysis."""
    cv = TextAreaField('Your CV/Resume', validators=[
        DataRequired(message="Please provide your CV/resume content")
    ])
    jd = TextAreaField('Job Description', validators=[
        DataRequired(message="Please provide the job description content")
    ])
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('fr', 'Français')
    ], default='en')
    rewrite_cv = BooleanField('Rewrite CV optimized for ATS', default=False)

class FeedbackForm(FlaskForm):
    """Form for user feedback submission."""
    email = StringField('Email (optional)', validators=[
        Optional()
        # Email validator removed to avoid dependency on email_validator package
    ])
    feedback = TextAreaField('Your Feedback', validators=[
        DataRequired(message="Please provide your feedback"),
        Length(min=10, message="Feedback must be at least 10 characters long")
    ])
    rating = SelectField('Rating', choices=[
        ('1', '1 - Poor'),
        ('2', '2 - Fair'),
        ('3', '3 - Average'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent')
    ], default='3')
