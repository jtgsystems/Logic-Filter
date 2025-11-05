"""
Comprehensive test suite for Logic Filter API.
Tests input validation, error handling, and API functionality.
"""

import pytest
from unittest.mock import Mock, patch
from api import app, validate_prompt_request, OLLAMA_MODELS


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'logic-filter-api'


class TestInputValidation:
    """Tests for input validation function."""

    def test_validate_empty_data(self):
        """Test validation fails with no data."""
        is_valid, error = validate_prompt_request(None)
        assert not is_valid
        assert "No JSON data provided" in error

    def test_validate_missing_prompt(self):
        """Test validation fails with missing prompt field."""
        is_valid, error = validate_prompt_request({'foo': 'bar'})
        assert not is_valid
        assert "Missing 'prompt' field" in error

    def test_validate_non_string_prompt(self):
        """Test validation fails with non-string prompt."""
        is_valid, error = validate_prompt_request({'prompt': 123})
        assert not is_valid
        assert "'prompt' must be a string" in error

    def test_validate_empty_prompt(self):
        """Test validation fails with empty prompt."""
        is_valid, error = validate_prompt_request({'prompt': '   '})
        assert not is_valid
        assert "'prompt' cannot be empty" in error

    def test_validate_too_long_prompt(self):
        """Test validation fails with oversized prompt."""
        is_valid, error = validate_prompt_request({'prompt': 'x' * 50001})
        assert not is_valid
        assert "exceeds maximum length" in error

    def test_validate_valid_prompt(self):
        """Test validation succeeds with valid prompt."""
        is_valid, error = validate_prompt_request({'prompt': 'test prompt'})
        assert is_valid
        assert error == ""


class TestProcessPromptEndpoint:
    """Tests for /process_prompt endpoint."""

    def test_process_prompt_missing_json(self, client):
        """Test endpoint returns 400 with no JSON."""
        response = client.post('/process_prompt')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_process_prompt_invalid_json(self, client):
        """Test endpoint returns 400 with invalid JSON."""
        response = client.post(
            '/process_prompt',
            data='not json',
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_process_prompt_missing_field(self, client):
        """Test endpoint returns 400 with missing prompt field."""
        response = client.post('/process_prompt', json={'foo': 'bar'})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_process_prompt_empty_prompt(self, client):
        """Test endpoint returns 400 with empty prompt."""
        response = client.post('/process_prompt', json={'prompt': ''})
        assert response.status_code == 400

    @patch('api.analyze_prompt')
    @patch('api.generate_solutions')
    @patch('api.vet_and_refine')
    @patch('api.finalize_prompt')
    @patch('api.enhance_prompt')
    @patch('api.comprehensive_review')
    def test_process_prompt_success(
        self, mock_comprehensive, mock_enhance, mock_finalize,
        mock_vet, mock_generate, mock_analyze, client
    ):
        """Test successful prompt processing."""
        # Mock all processing functions
        mock_analyze.return_value = "analysis"
        mock_generate.return_value = "solutions"
        mock_vet.return_value = "vetted"
        mock_finalize.return_value = "final"
        mock_enhance.return_value = "enhanced"
        mock_comprehensive.return_value = "comprehensive output"

        response = client.post('/process_prompt', json={'prompt': 'test prompt'})
        assert response.status_code == 200
        data = response.get_json()
        assert 'output' in data
        assert data['output'] == "comprehensive output"
        assert data['status'] == 'success'

        # Verify all functions were called
        mock_analyze.assert_called_once()
        mock_generate.assert_called_once()
        mock_vet.assert_called_once()
        mock_finalize.assert_called_once()
        mock_enhance.assert_called_once()
        mock_comprehensive.assert_called_once()

    @patch('api.analyze_prompt')
    def test_process_prompt_handles_errors(self, mock_analyze, client):
        """Test endpoint handles processing errors gracefully."""
        mock_analyze.side_effect = Exception("Test error")

        response = client.post('/process_prompt', json={'prompt': 'test'})
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data
        # Should not expose internal error details
        assert "Test error" not in data['error']


class TestConfiguration:
    """Tests for API configuration."""

    def test_ollama_models_configured(self):
        """Test that all required models are configured."""
        required_models = [
            "analysis", "generation", "vetting",
            "finalization", "enhancement", "comprehensive", "presenter"
        ]
        for model_type in required_models:
            assert model_type in OLLAMA_MODELS
            assert isinstance(OLLAMA_MODELS[model_type], str)
            assert len(OLLAMA_MODELS[model_type]) > 0