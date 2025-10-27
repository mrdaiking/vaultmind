"""
Adapter for auth0-ai-langchain integration.
WARNING: auth0-ai-langchain is NOT production-ready.
"""
from auth0_ai_langchain.auth0_ai import Auth0AI
from auth0_ai_langchain.federated_connections import get_access_token_for_connection
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Initialize Auth0 AI client
auth0_ai = Auth0AI()

# Decorator for Google Calendar token exchange
with_google_calendar_access = auth0_ai.with_federated_connection(
    connection="google-oauth2",
    scopes=[
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ]
)

async def get_google_token_via_langchain(user_id: str, refresh_token: str) -> Optional[str]:
    """
    Exchange refresh token for Google Calendar access token.
    Uses auth0_ai_langchain for token exchange.
    
    Note: This is experimental and may not work correctly.
    The auth0_ai_langchain package expects LangChain runnable context.
    """
    try:
        logger.info(f"[AUTH0_AI] Attempting token exchange for user {user_id}")
        
        # Try using get_access_token_for_connection with connection parameter
        # The auth0_ai_langchain library manages credentials internally via context
        access_token = get_access_token_for_connection(
            connection="google-oauth2"
        )
        
        if access_token:
            logger.info(f"[AUTH0_AI] ✅ Token exchanged successfully for user {user_id}")
            return access_token
        else:
            logger.warning(f"[AUTH0_AI] ⚠️ Token exchange returned None for user {user_id}")
            return None
        
    except Exception as e:
        logger.error(f"[AUTH0_AI][ERROR] Token exchange failed: {e}")
        logger.info(f"[AUTH0_AI] Will fallback to direct Auth0 API")
        return None