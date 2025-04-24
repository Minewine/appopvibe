"""
Test analyzer service functionality
"""
import pytest
from unittest.mock import AsyncMock, patch
from appopvibe.services.analyzer.analyzer_service import AnalyzerService
from appopvibe.services.llm.llm_service import LLMService

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing"""
    mock_service = AsyncMock(spec=LLMService)
    mock_service.generate.return_value = "Mock analysis result"
    mock_service.cached_generate.return_value = "Mock cached analysis result"
    return mock_service

@pytest.fixture
def analyzer_service(mock_llm_service):
    """Create an analyzer service with mock dependencies"""
    prompt_templates = {
        'en': {
            'analysis': 'Analyze CV: {cv} against JD: {jd}',
            'rewrite': 'Rewrite CV: {cv} for JD: {jd}'
        },
        'fr': {
            'analysis': 'Analysez CV: {cv} contre JD: {jd}',
            'rewrite': 'Réécrivez CV: {cv} pour JD: {jd}'
        }
    }
    return AnalyzerService(mock_llm_service, prompt_templates)

@pytest.mark.asyncio
async def test_analyze_cv_jd(analyzer_service, mock_llm_service):
    """Test that analyze_cv_jd calls LLM service with correct prompt"""
    # Setup
    cv_text = "My sample CV"
    jd_text = "Sample job description"
    
    # Execute
    result = await analyzer_service.analyze_cv_jd(cv_text, jd_text, 'en')
    
    # Verify
    assert result == "Mock cached analysis result"
    mock_llm_service.cached_generate.assert_called_once()
    call_args = mock_llm_service.cached_generate.call_args[1]
    assert 'prompt' in call_args
    assert cv_text in call_args['prompt']
    assert jd_text in call_args['prompt']

@pytest.mark.asyncio
async def test_rewrite_cv(analyzer_service, mock_llm_service):
    """Test that rewrite_cv calls LLM service with correct prompt"""
    # Setup
    cv_text = "My sample CV"
    jd_text = "Sample job description"
    
    # Execute
    result = await analyzer_service.rewrite_cv(cv_text, jd_text, 'en')
    
    # Verify
    assert result == "Mock analysis result"
    mock_llm_service.generate.assert_called_once()
    call_args = mock_llm_service.generate.call_args[1]
    assert 'prompt' in call_args
    assert cv_text in call_args['prompt']
    assert jd_text in call_args['prompt']

@pytest.mark.asyncio
async def test_process_submission_with_rewrite(analyzer_service):
    """Test process_submission with rewrite option"""
    # Mock the individual service methods
    analyzer_service.analyze_cv_jd = AsyncMock(return_value="Analysis result")
    analyzer_service.rewrite_cv = AsyncMock(return_value="Rewritten CV")
    
    # Execute
    result = await analyzer_service.process_submission(
        cv_text="My CV",
        jd_text="Job description",
        language="en",
        rewrite=True
    )
    
    # Verify
    assert result == {
        'analysis': 'Analysis result',
        'rewritten_cv': 'Rewritten CV'
    }
    analyzer_service.analyze_cv_jd.assert_called_once()
    analyzer_service.rewrite_cv.assert_called_once()
