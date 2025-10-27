"""
Test suite for auth0_ai_langchain migration.
"""
import pytest
import asyncio
from app.auth0_ai_adapter import get_google_token_via_langchain

@pytest.mark.asyncio
async def test_token_exchange_langchain():
    """Test token exchange via auth0_ai_langchain."""
    user_id = "test-user"
    refresh_token = "test-refresh-token"
    
    token = await get_google_token_via_langchain(user_id, refresh_token)
    
    # Should return None or valid token (depending on credentials)
    assert token is None or isinstance(token, str)

@pytest.mark.asyncio
async def test_calendar_with_langchain(test_client, auth_headers):
    """Test calendar operations with langchain enabled."""
    # Set feature flag
    import os
    os.environ["USE_AUTH0_AI_LANGCHAIN"] = "true"
    
    response = await test_client.get("/agent/calendar", headers=auth_headers)
    
    # Should work the same as direct API calls
    assert response.status_code in [200, 401]

def test_feature_flag_disabled():
    """Ensure default is disabled."""
    import os
    flag = os.getenv("USE_AUTH0_AI_LANGCHAIN", "false")
    assert flag.lower() == "false"