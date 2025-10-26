"""
Test configuration and fixtures
"""
import os
import pytest
from typing import Dict, Any
from datetime import datetime

# Set test environment variables
os.environ["AUTH0_DOMAIN"] = "test-domain.auth0.com"
os.environ["AUTH0_CLIENT_ID"] = "test_client_id"
os.environ["AUTH0_CLIENT_SECRET"] = "test_client_secret"
os.environ["AUTH0_AUDIENCE"] = "https://test-api"
os.environ["OPENAI_API_KEY"] = "test_openai_key"


@pytest.fixture
def mock_jwt_payload() -> Dict[str, Any]:
    """Mock JWT payload for testing"""
    return {
        "sub": "google-oauth2|123456789",
        "email": "test@example.com",
        "iss": "https://test-domain.auth0.com/",
        "aud": "https://test-api",
        "exp": int((datetime.utcnow().timestamp())) + 3600,
    }


@pytest.fixture
def mock_google_token() -> str:
    """Mock Google OAuth token"""
    return "mock_google_access_token"


@pytest.fixture
def sample_event() -> Dict[str, Any]:
    """Sample calendar event for testing"""
    return {
        "title": "Test Meeting",
        "description": "Test description",
        "start_time": "2025-10-27T10:00:00Z",
        "end_time": "2025-10-27T11:00:00Z",
    }
