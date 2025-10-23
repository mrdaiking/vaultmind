"""
Auth0 Management API integration to fetch Google access tokens
"""
import os
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache for Management API token
_mgmt_token_cache = {
    "token": None,
    "expires_at": None
}

async def get_management_api_token() -> str:
    """Get Auth0 Management API access token with caching"""
    
    # Check cache
    if _mgmt_token_cache["token"] and _mgmt_token_cache["expires_at"]:
        if datetime.now() < _mgmt_token_cache["expires_at"]:
            return _mgmt_token_cache["token"]
    
    # Request new token
    auth0_domain = os.getenv("AUTH0_DOMAIN")
    client_id = os.getenv("AUTH0_CLIENT_ID")
    client_secret = os.getenv("AUTH0_CLIENT_SECRET")
    
    if not all([auth0_domain, client_id, client_secret]):
        raise ValueError("Missing Auth0 credentials for Management API")
    
    logger.info(f"🔑 Requesting Management API token...")
    logger.info(f"   Domain: {auth0_domain}")
    logger.info(f"   Client ID: {client_id[:20]}...")
    logger.info(f"   Audience: https://{auth0_domain}/api/v2/")
    
    async with httpx.AsyncClient() as client:
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": f"https://{auth0_domain}/api/v2/",
            "grant_type": "client_credentials"
        }
        
        response = await client.post(
            f"https://{auth0_domain}/oauth/token",
            json=payload
        )
        
        if response.status_code != 200:
            logger.error(f"❌ Auth0 Management API token request failed!")
            logger.error(f"   Status: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            logger.error(f"")
            logger.error(f"⚠️  ACTION REQUIRED:")
            logger.error(f"   1. Go to Auth0 Dashboard → Applications → APIs")
            logger.error(f"   2. Click 'Auth0 Management API'")
            logger.error(f"   3. Go to 'Machine to Machine Applications' tab")
            logger.error(f"   4. Find your app (VaultMind) and TOGGLE IT ON ✅")
            logger.error(f"   5. Expand dropdown and check: read:users, read:user_idp_tokens")
            logger.error(f"   6. Click 'Update'")
            logger.error(f"")
        
        response.raise_for_status()
        data = response.json()
        
        # Cache the token (expires in 24 hours typically)
        _mgmt_token_cache["token"] = data["access_token"]
        _mgmt_token_cache["expires_at"] = datetime.now() + timedelta(seconds=data.get("expires_in", 86400) - 300)  # 5 min buffer
        
        return data["access_token"]


async def get_google_access_token_from_management_api(user_sub: str) -> Optional[str]:
    """
    Fetch Google access token for a user via Auth0 Management API
    
    Args:
        user_sub: The user's 'sub' claim from JWT (e.g., 'google-oauth2|115526030469434638320')
    
    Returns:
        Google access token if found, None otherwise
    """
    try:
        auth0_domain = os.getenv("AUTH0_DOMAIN")
        mgmt_token = await get_management_api_token()
        
        # Encode the user_id properly (replace | with %7C)
        encoded_user_id = user_sub.replace("|", "%7C")
        
        async with httpx.AsyncClient() as client:
            # Get user details including identities
            response = await client.get(
                f"https://{auth0_domain}/api/v2/users/{encoded_user_id}",
                headers={
                    "Authorization": f"Bearer {mgmt_token}"
                },
                params={
                    "fields": "identities",
                    "include_fields": "true"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch user from Management API: {response.status_code} {response.text}")
                return None
            
            user_data = response.json()
            identities = user_data.get("identities", [])
            
            # Find Google identity
            for identity in identities:
                if identity.get("provider") == "google-oauth2":
                    access_token = identity.get("access_token")
                    if access_token:
                        logger.info("✅ Found Google access token via Management API")
                        return access_token
                    else:
                        logger.warning("❌ Google identity found but no access_token property")
            
            logger.warning("❌ No Google identity found in Management API response")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching Google token from Management API: {e}")
        return None
