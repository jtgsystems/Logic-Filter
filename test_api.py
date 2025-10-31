import pytest
from unittest.mock import patch
from api import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('processing_functions.get_ollama_manager')
def test_process_prompt(mock_get_manager, client):
    # Mock the chat method to return a dummy response
    mock_manager = mock_get_manager.return_value
    mock_manager.chat.return_value = {"message": {"content": "processed prompt"}}

    response = client.post('/process_prompt', json={'prompt': 'test prompt'})

    assert response.status_code == 200
    data = response.get_json()
    assert 'output' in data
    assert data['output'] == 'processed prompt'
