"""
Configuration settings for the CV Analyzer application.
Uses environment variables with sensible defaults.
"""
import os
import logging
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / 'reports'
FEEDBACK_DIR = BASE_DIR / 'feedback'

# Ensure directories exist
REPORTS_DIR.mkdir(exist_ok=True)
FEEDBACK_DIR.mkdir(exist_ok=True)

class Config:
    """Base configuration class with common settings."""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'REPLACE_THIS_WITH_A_VERY_STRONG_RANDOM_KEY')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # Application settings
    MAX_CONTENT_SIZE_KB = int(os.getenv('MAX_CONTENT_SIZE_KB', 30))
    MAX_CONTENT_LENGTH = MAX_CONTENT_SIZE_KB * 1024
    REPORT_RETENTION_DAYS = int(os.getenv('REPORT_RETENTION_DAYS', 30))
    
    # LLM API settings
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'deepseek/deepseek-chat-v3-0324')
    BACKUP_MODEL = os.getenv('BACKUP_MODEL', 'mistralai/mistral-7b-instruct')
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'fr': 'Français'
    }
    
    # Log key loading status (securely)
    @classmethod
    def log_api_keys(cls):
        if cls.OPENROUTER_API_KEY:
            key_preview = cls.OPENROUTER_API_KEY[:4] + "..." + cls.OPENROUTER_API_KEY[-3:] if len(cls.OPENROUTER_API_KEY) > 7 else "[too short]"
            logging.info(f"OpenRouter API Key loaded: {key_preview}")
        else:
            logging.warning("OPENROUTER_API_KEY not set")
        
        if cls.GROQ_API_KEY:
            key_preview = cls.GROQ_API_KEY[:4] + "..." + cls.GROQ_API_KEY[-3:] if len(cls.GROQ_API_KEY) > 7 else "[too short]"
            logging.info(f"Groq API Key loaded: {key_preview}")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds


# Set default config based on environment
config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

# Get config class based on environment variable
def get_config():
    """Get configuration class based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)
