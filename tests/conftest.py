import pytest
from api.factory import create_app

@pytest.fixture
def test_client():
    app = create_app()
    app.config.update({"TESTING": True})
    return app.test_client()