import pytest

from api import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_process_prompt(client):
    response = client.post('/process_prompt', json={'prompt': 'test prompt'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'output' in data
