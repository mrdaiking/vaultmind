"""
VaultMind FastAPI Backend
Secure AI Agent with Auth0 JWT validation and Token Vault integration
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
import asyncio
import json

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import Google Calendar integration
from google_calendar import GoogleCalendarClient, get_google_access_token_from_auth0

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security models
security = HTTPBearer()

# Global variables for JWKS cache
jwks_cache = {}
jwks_last_updated = None
JWKS_CACHE_DURATION = 3600  # 1 hour in seconds

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)

class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[str] = None
    success: bool
    timestamp: datetime

class CalendarEvent(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str  # ISO format
    end_time: str    # ISO format

class AuditLog:
    """In-memory audit log for agent actions"""
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
    
    def log_action(self, user_id: str, action: str, details: Dict[str, Any], success: bool):
        """Log an agent action with security context"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details,
            "success": success,
            "ip_address": "127.0.0.1",  # Would be extracted from request in production
        }
        self.logs.append(log_entry)
        logger.info(f"Action logged: {action} for user {user_id} - Success: {success}")
    
    def get_user_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Get audit logs for a specific user"""
        return [log for log in self.logs if log["user_id"] == user_id]

# Global audit log instance
audit_log = AuditLog()

async def get_jwks():
    """
    Fetch and cache Auth0 JWKS for JWT verification
    Security: Validates JWT signatures against Auth0's public keys
    """
    global jwks_cache, jwks_last_updated
    
    current_time = datetime.utcnow().timestamp()
    
    # Return cached JWKS if still valid
    if jwks_cache and jwks_last_updated and (current_time - jwks_last_updated) < JWKS_CACHE_DURATION:
        return jwks_cache
    
    auth0_domain = os.getenv("AUTH0_DOMAIN")
    if not auth0_domain:
        raise HTTPException(status_code=500, detail="AUTH0_DOMAIN not configured")
    
    jwks_url = f"https://{auth0_domain}/.well-known/jwks.json"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks_cache = response.json()
            jwks_last_updated = current_time
            logger.info("JWKS cache updated successfully")
            return jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        raise HTTPException(status_code=500, detail="Unable to verify JWT signature")

async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Verify Auth0 JWT token and extract user claims
    Security: Validates JWT signature, issuer, audience, and expiration
    """
    token = credentials.credentials
    
    try:
        # Get JWKS for signature verification
        jwks = await get_jwks()
        
        # Decode JWT header to get kid (key ID)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        logger.info(f"Verifying JWT with kid: {kid}")
        
        # Also decode payload without verification to see what's inside
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        logger.info(f"Token audience claim: {unverified_payload.get('aud')}")
        logger.info(f"Token issuer claim: {unverified_payload.get('iss')}")
        
        if not kid:
            raise HTTPException(status_code=401, detail="JWT missing key ID")
        
        # Find the correct key in JWKS
        rsa_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = {
                    "kty": key.get("kty"),
                    "kid": key.get("kid"),
                    "use": key.get("use"),
                    "n": key.get("n"),
                    "e": key.get("e")
                }
                break
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Unable to find appropriate key")
        
        # Construct the public key
        public_key = RSAAlgorithm.from_jwk(json.dumps(rsa_key))
        
        # Verify and decode JWT
        auth0_domain = os.getenv("AUTH0_DOMAIN")
        auth0_audience = os.getenv("AUTH0_AUDIENCE")
        
        logger.info(f"Validating JWT - Domain: {auth0_domain}, Audience: {auth0_audience}")
        
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=auth0_audience,
            issuer=f"https://{auth0_domain}/"
        )
        
        logger.info(f"JWT verified for user: {payload.get('sub', 'unknown')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.error("JWT token has expired")
        raise HTTPException(status_code=401, detail="JWT token has expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT validation failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid JWT token: {str(e)}")
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"JWT verification error: {type(e).__name__}: {e}")
        logger.exception("Full traceback:")  # This will print the full stack trace
        raise HTTPException(status_code=401, detail=f"Unable to verify JWT token: {str(e)}")

async def exchange_token_with_vault(user_jwt: str, provider: str = "google") -> str:
    """
    Exchange Auth0 JWT for short-lived provider token via Token Vault
    Security: Never stores refresh tokens, only short-lived access tokens
    """
    # This is a placeholder for Token Vault integration
    # In production, this would call your Token Vault API
    
    vault_endpoint = os.getenv("TOKEN_VAULT_ENDPOINT", "https://your-token-vault.com/exchange")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                vault_endpoint,
                json={
                    "auth0_token": user_jwt,
                    "provider": provider,
                    "scopes": ["https://www.googleapis.com/auth/calendar"]
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"Token Vault exchange failed: {response.status_code}")
                raise HTTPException(status_code=500, detail="Token exchange failed")
            
            token_data = response.json()
            return token_data.get("access_token")
            
    except httpx.RequestError as e:
        logger.error(f"Token Vault request failed: {e}")
        # For MVP/demo purposes, return a mock token
        logger.warning("Using mock token for demo purposes")
        return "mock_google_access_token_for_demo"

class AIAgent:
    """
    AI Agent for processing natural language commands
    Security: Validates and sanitizes all inputs before API calls
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured - using keyword-based intent detection")
        self.model = "gpt-4o-mini"  # Fast and cost-effective
    
    async def process_message(self, message: str, user_id: str, user_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message and determine action to take
        Security: Input validation and action whitelisting
        """
        message = message.strip()
        
        # Use OpenAI for intent detection if available
        if self.openai_api_key:
            return await self._process_with_openai(message, user_id, user_claims)
        
        # Fallback: Simple keyword-based intent detection
        if any(keyword in message.lower() for keyword in ["calendar", "event", "meeting", "appointment"]):
            if any(keyword in message.lower() for keyword in ["create", "add", "schedule"]):
                return await self._handle_calendar_creation(message, user_id, user_claims)
            elif any(keyword in message.lower() for keyword in ["list", "show", "view"]):
                return await self._handle_calendar_list(user_id, user_claims)
        
        # Default response for non-calendar queries
        return {
            "response": f"I understand you said: '{message}'. I can help you with calendar events. Try asking me to 'create a meeting' or 'show my calendar'.",
            "action_taken": "general_response",
            "success": True
        }
    
    async def _process_with_openai(self, message: str, user_id: str, user_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Use OpenAI to understand intent and extract parameters"""
        try:
            # Get current datetime for context
            now = datetime.utcnow()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")
            current_day = now.strftime("%A")  # e.g., "Wednesday"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": f"""You are an AI assistant that helps with calendar management. 

IMPORTANT: Today's date is {current_date} ({current_day}) at {current_time} UTC.

Analyze the user's message and respond with a JSON object containing:
{{
  "intent": "list_calendar" | "create_event" | "general",
  "parameters": {{
    "title": "event title (for create)",
    "start_time": "ISO 8601 datetime with timezone (for create)",
    "end_time": "ISO 8601 datetime with timezone (for create)",
    "description": "event description (for create)"
  }},
  "response": "friendly response to user"
}}

For date/time parsing (ALWAYS use {current_date} as reference):
- "tomorrow at 3pm" → {current_date} + 1 day at 15:00 in ISO format with timezone
- "next Tuesday" → calculate from {current_date}
- "today at 2pm" → {current_date} at 14:00
- If time not specified, default to 10:00 AM
- If duration not specified, default to 1 hour
- ALWAYS include timezone in ISO format (e.g., 2025-10-23T15:00:00+09:00)

Only use intents: list_calendar, create_event, or general."""
                            },
                            {
                                "role": "user",
                                "content": message
                            }
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.7
                    },
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    raise Exception("OpenAI API request failed")
                
                result = response.json()
                ai_response = json.loads(result["choices"][0]["message"]["content"])
                
                intent = ai_response.get("intent", "general")
                params = ai_response.get("parameters", {})
                ai_message = ai_response.get("response", "I'm not sure how to help with that.")
                
                # Route to appropriate handler based on intent
                if intent == "list_calendar":
                    return await self._handle_calendar_list(user_id, user_claims)
                elif intent == "create_event":
                    return await self._handle_calendar_creation_with_params(params, user_id, user_claims, ai_message)
                else:
                    return {
                        "response": ai_message,
                        "action_taken": "general_response",
                        "success": True
                    }
                    
        except Exception as e:
            logger.error(f"OpenAI processing error: {e}")
            # Fallback to keyword detection
            if any(keyword in message.lower() for keyword in ["calendar", "show", "list", "view"]):
                return await self._handle_calendar_list(user_id, user_claims)
            return {
                "response": "I had trouble understanding that. Could you try rephrasing?",
                "action_taken": "error",
                "success": False
            }
    
    async def _handle_calendar_creation_with_params(
        self, 
        params: Dict[str, Any], 
        user_id: str, 
        user_claims: Optional[Dict[str, Any]], 
        ai_message: str
    ) -> Dict[str, Any]:
        """Create calendar event with OpenAI-extracted parameters"""
        try:
            title = params.get("title", "Untitled Event")
            start_time = params.get("start_time")
            end_time = params.get("end_time")
            description = params.get("description")
            
            if not start_time or not end_time:
                return {
                    "response": "I need more information about when to schedule this event. Could you provide a date and time?",
                    "action_taken": "calendar_create",
                    "success": False
                }
            
            # Get Google access token
            google_token = await get_google_access_token_from_auth0(user_claims) if user_claims else None
            
            if not google_token:
                # Log without creating
                audit_log.log_action(
                    user_id=user_id,
                    action="calendar_create_attempt",
                    details={"title": title, "note": "No Google token - would create in real calendar"},
                    success=True
                )
                return {
                    "response": f"I would create: '{title}' on {start_time}. (Demo mode - authenticate with Google Calendar to create real events)",
                    "action_taken": "calendar_create",
                    "success": True
                }
            
            # Create real event
            calendar_client = GoogleCalendarClient(google_token)
            event = await calendar_client.create_event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description
            )
            
            audit_log.log_action(
                user_id=user_id,
                action="calendar_create",
                details={"title": title, "start": start_time, "event_id": event.get("id")},
                success=True
            )
            
            return {
                "response": f"✅ Created: '{title}' on {start_time}",
                "action_taken": "calendar_create",
                "success": True,
                "event": event
            }
            
        except Exception as e:
            logger.error(f"Calendar creation error: {e}")
            return {
                "response": "I had trouble creating that event. Please try again.",
                "action_taken": "calendar_create",
                "success": False
            }
    
    async def _handle_calendar_creation(self, message: str, user_id: str, user_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle calendar event creation (keyword-based fallback)"""
        try:
            # Simple extraction from message
            event_title = message[:100] if len(message) <= 100 else f"{message[:97]}..."
            
            # Log the action attempt
            audit_log.log_action(
                user_id=user_id,
                action="calendar_create_attempt",
                details={"message": message, "event_title": event_title},
                success=True
            )
            
            return {
                "response": f"I would create a calendar event: '{event_title}'. To create real events, please add an OpenAI API key or provide more details like date and time.",
                "action_taken": "calendar_create",
                "success": True
            }
            
        except Exception as e:
            audit_log.log_action(
                user_id=user_id,
                action="calendar_create_attempt",
                details={"message": message, "error": str(e)},
                success=False
            )
            return {
                "response": "I encountered an error while trying to create the calendar event.",
                "action_taken": "calendar_create",
                "success": False
            }
    
    async def _handle_calendar_list(self, user_id: str, user_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        """Handle calendar listing - actually fetch calendar events"""
        try:
            if not user_claims:
                return {
                    "response": "I need authentication info to access your calendar.",
                    "action_taken": "calendar_list",
                    "success": False
                }
            
            # Extract Google access token from Auth0 user claims
            print("User Claims in AI Agent:", user_claims)

            # get_google_access_token_from_auth0 is now async
            google_token = await get_google_access_token_from_auth0(user_claims)

            print("Google Token in AI Agent:", google_token)
            
            if not google_token:
                # Fallback to mock data if no Google token
                logger.warning("No Google token found, using mock calendar data")
                events = [
                    {
                        "title": "Demo Event 1",
                        "start": "2025-10-21T09:00:00Z"
                    },
                    {
                        "title": "Demo Event 3", 
                        "start": "2025-10-21T14:00:00Z"
                    }
                ]
                response_text = "Here are your upcoming events (Mock Data - add Calendar scopes to see real events):\n\n"
                for i, event in enumerate(events, 1):
                    response_text += f"{i}. {event['title']} at {event['start']}\n"
            else:
                # Use real Google Calendar API
                calendar_client = GoogleCalendarClient(google_token)
                events = await calendar_client.list_events(max_results=10)
                
                if not events:
                    response_text = "You have no upcoming calendar events."
                else:
                    response_text = f"Here are your {len(events)} upcoming events:\n\n"
                    for i, event in enumerate(events, 1):
                        response_text += f"{i}. {event['title']} at {event['start']}\n"
            
            # Log the action
            audit_log.log_action(
                user_id=user_id,
                action="calendar_list_attempt",
                details={"events_count": len(events), "real_data": bool(google_token)},
                success=True
            )
            
            return {
                "response": response_text,
                "action_taken": "calendar_list",
                "success": True,
                "events": events  # Include actual event data
            }
            
        except Exception as e:
            logger.error(f"Calendar list error in AI agent: {e}")
            audit_log.log_action(
                user_id=user_id,
                action="calendar_list_attempt",
                details={"error": str(e)},
                success=False
            )
            return {
                "response": "I encountered an error while retrieving your calendar events.",
                "action_taken": "calendar_list",
                "success": False
            }

# Initialize AI agent
ai_agent = AIAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("VaultMind backend starting up...")
    # Pre-load JWKS on startup for faster first request
    try:
        await get_jwks()
        logger.info("JWKS preloaded successfully")
    except Exception as e:
        logger.warning(f"Failed to preload JWKS: {e}")
    
    yield
    
    logger.info("VaultMind backend shutting down...")

# Initialize FastAPI app
app = FastAPI(
    title="VaultMind API",
    description="Secure AI Agent with Auth0 JWT validation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://frontend-seven-neon-54.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/agent/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest,
    user_claims: Dict[str, Any] = Depends(verify_jwt)
):
    """
    Chat with AI agent endpoint
    Security: Requires valid Auth0 JWT, validates input, logs all actions
    """
    user_id = user_claims.get("sub", "unknown")
    
    try:
        # Process message with AI agent
        result = await ai_agent.process_message(request.message, user_id, user_claims)
        
        # Log the chat interaction
        audit_log.log_action(
            user_id=user_id,
            action="chat_interaction",
            details={
                "message": request.message,
                "response": result["response"],
                "action_taken": result.get("action_taken")
            },
            success=result["success"]
        )
        
        return ChatResponse(
            response=result["response"],
            action_taken=result.get("action_taken"),
            success=result["success"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        audit_log.log_action(
            user_id=user_id,
            action="chat_interaction",
            details={"message": request.message, "error": str(e)},
            success=False
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/agent/calendar")
async def list_calendar_events(
    user_claims: Dict[str, Any] = Depends(verify_jwt)
):
    """
    List calendar events endpoint
    Security: Requires valid JWT, uses Google OAuth2 token from Auth0
    """
    user_id = user_claims.get("sub", "unknown")
    
    try:
        # Extract Google access token from Auth0 user claims
        google_token = get_google_access_token_from_auth0(user_claims)
        
        if not google_token:
            # Fallback to mock data if no Google token
            logger.warning("No Google token found, using mock calendar data")
            events = [
                {
                    "id": "mock-1",
                    "title": "Demo Event (Mock Data)",
                    "description": "Re-authenticate with Google Calendar scopes to see real events",
                    "start": "2025-10-20T09:00:00Z",
                    "end": "2025-10-20T10:00:00Z"
                }
            ]
        else:
            # Use real Google Calendar API
            calendar_client = GoogleCalendarClient(google_token)
            events = await calendar_client.list_events(max_results=10)
        
        audit_log.log_action(
            user_id=user_id,
            action="calendar_list",
            details={"events_count": len(events), "real_data": bool(google_token)},
            success=True
        )
        
        return {"events": events, "success": True, "real_data": bool(google_token)}
        
    except Exception as e:
        logger.error(f"Calendar list error: {e}")
        audit_log.log_action(
            user_id=user_id,
            action="calendar_list",
            details={"error": str(e)},
            success=False
        )
        raise HTTPException(status_code=500, detail=f"Unable to retrieve calendar events: {str(e)}")

@app.post("/agent/calendar")
async def create_calendar_event(
    event: CalendarEvent,
    user_claims: Dict[str, Any] = Depends(verify_jwt)
):
    """
    Create calendar event endpoint
    Security: Requires valid JWT, validates event data, uses Google Calendar API
    """
    user_id = user_claims.get("sub", "unknown")
    
    try:
        # Extract Google access token from Auth0 user claims
        google_token = get_google_access_token_from_auth0(user_claims)
        
        if not google_token:
            # Fallback to mock event creation
            logger.warning("No Google token found, creating mock calendar event")
            created_event = {
                "id": f"mock-event-{datetime.utcnow().timestamp()}",
                "title": event.title,
                "description": event.description or "Mock event - Re-authenticate to create real events",
                "start": event.start_time,
                "end": event.end_time,
                "created": datetime.utcnow().isoformat(),
                "is_mock": True
            }
        else:
            # Use real Google Calendar API
            calendar_client = GoogleCalendarClient(google_token)
            created_event = await calendar_client.create_event(
                title=event.title,
                start_time=event.start_time,
                end_time=event.end_time,
                description=event.description
            )
            created_event["is_mock"] = False
        
        audit_log.log_action(
            user_id=user_id,
            action="calendar_create",
            details={
                "event_title": event.title,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "real_data": bool(google_token)
            },
            success=True
        )
        
        return {"event": created_event, "success": True, "real_data": bool(google_token)}
        
    except Exception as e:
        logger.error(f"Calendar create error: {e}")
        audit_log.log_action(
            user_id=user_id,
            action="calendar_create",
            details={"error": str(e), "event_title": event.title},
            success=False
        )
        raise HTTPException(status_code=500, detail=f"Unable to create calendar event: {str(e)}")

@app.get("/audit/logs")
async def get_audit_logs(
    user_claims: Dict[str, Any] = Depends(verify_jwt)
):
    """
    Get audit logs for the authenticated user
    Security: Users can only see their own audit logs
    """
    user_id = user_claims.get("sub", "unknown")
    
    try:
        user_logs = audit_log.get_user_logs(user_id)
        return {"logs": user_logs, "count": len(user_logs)}
        
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve audit logs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)