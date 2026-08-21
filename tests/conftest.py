import pytest
from main import app

@pytest.fixture
def test_client():
    app.config.update({"TESTING": True})
    return app.test_client()