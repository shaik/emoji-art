import pytest
from app import create_app

@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app()
    app.config.update({
        'TESTING': True,
    })
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()
