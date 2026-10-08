"""
Form models for the CV Analyzer application.
"""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, BooleanField, StringField
from wtforms.validators import DataRequired, Optional, Length

MAX_FIELD_CHARS = 12000


class CVAnalysisForm(FlaskForm):
    """Form for CV vs Job Description analysis."""
    cv = TextAreaField('Your CV/Resume', validators=[
        DataRequired(message="Please provide your CV/resume content"),
        Length(min=40, max=MAX_FIELD_CHARS, message=f"CV must be 40–{MAX_FIELD_CHARS} characters"),
    ])
    jd = TextAreaField('Job Description', validators=[
        DataRequired(message="Please provide the job description content"),
        Length(min=40, max=MAX_FIELD_CHARS, message=f"Job description must be 40–{MAX_FIELD_CHARS} characters"),
    ])
    language = SelectField('Language', choices=[
        ('en', 'English'),
        ('fr', 'Français')
    ], default='en')
    rewrite_cv = BooleanField('Rewrite CV optimized for ATS', default=False)


class FeedbackForm(FlaskForm):
    """Form for user feedback submission."""
    email = StringField('Email (optional)', validators=[Optional()])
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
