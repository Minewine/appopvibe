"""
CV analyzer service that processes CVs and job descriptions.
"""
import logging
from typing import Dict, Any, Optional, Tuple
import hashlib

from appopvibe.services.llm.llm_service import LLMService

class AnalyzerService:
    """Service for analyzing CV and job description matches."""
    
    def __init__(self, llm_service: LLMService, prompt_templates: Dict[str, Dict[str, str]]):
        """Initialize the analyzer service.
        
        Args:
            llm_service: The LLM service for generating text
            prompt_templates: Dictionary of prompt templates keyed by language
        """
        self.llm_service = llm_service
        self.prompt_templates = prompt_templates
        self.logger = logging.getLogger(__name__)
    
    def _get_prompt_template(self, language: str, template_type: str) -> str:
        """Get the appropriate prompt template based on language and type."""
        try:
            return self.prompt_templates[language][template_type]
        except KeyError:
            self.logger.warning(f"Template not found for {language}/{template_type}, falling back to English")
            return self.prompt_templates['en'][template_type]
    
    def _create_hash(self, text: str) -> str:
        """Create a hash of the given text for caching purposes."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    async def analyze_cv_jd(self, cv_text: str, jd_text: str, 
                          language: str = 'en') -> str:
        """Analyze a CV against a job description.
        
        Args:
            cv_text: The CV text content
            jd_text: The job description text content
            language: The language code (e.g., 'en', 'fr')
            
        Returns:
            Analysis results as a formatted string
        """
        self.logger.info(f"Analyzing CV ({len(cv_text)} chars) against JD ({len(jd_text)} chars) in {language}")
        
        # Get the appropriate prompt template
        analysis_template = self._get_prompt_template(language, 'analysis')
        
        # Create prompt from template
        analysis_prompt = analysis_template.format(cv=cv_text, jd=jd_text)
        
        # Generate analysis using LLM service
        cv_hash = self._create_hash(cv_text)
        jd_hash = self._create_hash(jd_text)
        
        # Use cached version if available to save API costs
        analysis_result = await self.llm_service.cached_generate(
            prompt=analysis_prompt, 
            temperature=0.2  # Lower temperature for more consistent analysis
        )
        
        self.logger.info(f"Analysis completed, result length: {len(analysis_result)}")
        return analysis_result
    
    async def rewrite_cv(self, cv_text: str, jd_text: str,
                       language: str = 'en') -> str:
        """Rewrite a CV optimized for the given job description.
        
        Args:
            cv_text: The CV text content
            jd_text: The job description text content
            language: The language code (e.g., 'en', 'fr')
            
        Returns:
            Rewritten CV text
        """
        self.logger.info(f"Rewriting CV in {language}")
        
        # Get the appropriate prompt template
        rewrite_template = self._get_prompt_template(language, 'rewrite')
        
        # Create prompt from template
        rewrite_prompt = rewrite_template.format(cv=cv_text, jd=jd_text)
        
        # Generate rewrite using LLM service
        rewrite_result = await self.llm_service.generate(
            prompt=rewrite_prompt,
            temperature=0.4  # Moderate temperature for creativity but relevance
        )
        
        self.logger.info(f"CV rewriting completed, result length: {len(rewrite_result)}")
        return rewrite_result
        
    async def process_submission(self, cv_text: str, jd_text: str,
                              language: str = 'en', rewrite: bool = False) -> Dict[str, str]:
        """Process a complete submission including analysis and optional CV rewriting.
        
        Args:
            cv_text: The CV text content
            jd_text: The job description text content
            language: The language code (e.g., 'en', 'fr')
            rewrite: Whether to include CV rewriting
            
        Returns:
            Dict with analysis and optionally rewritten CV
        """
        self.logger.info(f"Processing submission (rewrite={rewrite})")
        
        # Start analysis
        analysis_task = self.analyze_cv_jd(cv_text, jd_text, language)
        
        # If rewrite requested, start that too
        rewrite_task = None
        if rewrite:
            rewrite_task = self.rewrite_cv(cv_text, jd_text, language)
        
        # Wait for analysis to complete
        analysis = await analysis_task
        
        # Wait for rewrite if requested
        rewritten_cv = None
        if rewrite_task:
            rewritten_cv = await rewrite_task
            
        # Build result
        result = {
            'analysis': analysis
        }
        
        if rewritten_cv:
            result['rewritten_cv'] = rewritten_cv
            
        return result
