"""
Created by Felix
Date: 2025-10-25
Description:
VaultMind FastAPI Backend
Secure AI Agent with Auth0 JWT validation and Token Vault integration
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Security, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
import asyncio
import json
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from openai import OpenAI

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Import Google Calendar integration
from app.google_calendar import GoogleCalendarClient, get_google_access_token_from_auth0

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)

# Security models
security = HTTPBearer()

# Global variables for JWKS cache
jwks_cache = {}
jwks_last_updated = None
JWKS_CACHE_DURATION = 3600  # 1 hour in seconds


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    timezone: Optional[str] = Field(default="UTC", description="User's timezone (IANA format)")


class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[str] = None
    success: bool
    timestamp: datetime
    event_details: Optional[Dict[str, Any]] = None  # Single event details for created events
    events: Optional[List[Dict[str, Any]]] = None  # Multiple events for list operations
    conflicts: Optional[List[Dict[str, Any]]] = None  # Conflicting events (if any)


class CalendarEvent(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: str  # ISO format
    end_time: str  # ISO format


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
    if (
        jwks_cache
        and jwks_last_updated
        and (current_time - jwks_last_updated) < JWKS_CACHE_DURATION
    ):
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


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Dict[str, Any]:
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
                    "e": key.get("e"),
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
            issuer=f"https://{auth0_domain}/",
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
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    async def process_message(
        self,
        message: str,
        user_id: str,
        user_claims: Optional[Dict[str, Any]] = None,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """
        Process user message and determine action to take
        Security: Input validation, moderation check, and action whitelisting
        """
        message = message.strip()

        # 🛡️ SECURITY: Check for harmful content using OpenAI Moderation API
        if self.openai_client:
            try:
                moderation_result = await self._moderate_content(message, user_id)
                if moderation_result["flagged"]:
                    logger.warning(f"[MODERATION] Blocked harmful content from user {user_id}")
                    logger.warning(f"[MODERATION] Categories: {moderation_result['categories']}")
                    return {
                        "response": "I'm sorry, but I cannot process that request. Please keep conversations professional and calendar-related.",
                        "action_taken": "moderation_blocked",
                        "success": False,
                    }
            except Exception as e:
                logger.error(f"[MODERATION][ERROR] Moderation check failed: {e}")
                # Continue processing if moderation fails (fail-open approach)

        # Use OpenAI for intent detection if available
        if self.openai_api_key:
            return await self._process_with_openai(message, user_id, user_claims, timezone)

        # Fallback: Simple keyword-based intent detection
        if any(
            keyword in message.lower()
            for keyword in ["calendar", "event", "meeting", "appointment"]
        ):
            if any(keyword in message.lower() for keyword in ["create", "add", "schedule"]):
                return await self._handle_calendar_creation(message, user_id, user_claims, timezone)
            elif any(keyword in message.lower() for keyword in ["list", "show", "view"]):
                return await self._handle_calendar_list(user_id, user_claims)

        # Default response for non-calendar queries
        return {
            "response": f"I understand you said: '{message}'. I can help you with calendar events. Try asking me to 'create a meeting' or 'show my calendar'.",
            "action_taken": "general_response",
            "success": True,
        }

    async def _moderate_content(self, message: str, user_id: str) -> Dict[str, Any]:
        """
        Check message for harmful content using OpenAI Moderation API
        
        Returns:
            Dict with 'flagged' (bool) and 'categories' (list of flagged categories)
        """
        try:
            response = self.openai_client.moderations.create(
                model="omni-moderation-latest",
                input=message
            )
            
            result = response.results[0]
            
            # Extract flagged categories
            flagged_categories = []
            if result.flagged:
                categories = result.categories.model_dump()
                flagged_categories = [
                    category for category, is_flagged in categories.items() 
                    if is_flagged
                ]
            
            return {
                "flagged": result.flagged,
                "categories": flagged_categories
            }
            
        except Exception as e:
            logger.error(f"[MODERATION][ERROR] Moderation API call failed: {e}")
            # Fail-open: If moderation fails, don't block the message
            return {"flagged": False, "categories": []}

    async def _process_with_openai(
        self,
        message: str,
        user_id: str,
        user_claims: Optional[Dict[str, Any]] = None,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """Use OpenAI to understand intent and extract parameters"""
        try:
            # Get current datetime for user's timezone
            from zoneinfo import ZoneInfo

            try:
                tz = ZoneInfo(timezone)
            except:
                logger.warning(f"Invalid timezone {timezone}, using UTC")
                tz = ZoneInfo("UTC")

            now = datetime.now(tz)
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")
            current_day = now.strftime("%A")  # e.g., "Wednesday"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": f"""You are an AI assistant that helps with calendar management. 

IMPORTANT: Today's date is {current_date} ({current_day}) at {current_time} in timezone {timezone}.

Analyze the user's message and respond with a JSON object containing:
{{
  "intent": "list_calendar" | "create_event" | "general",
  "parameters": {{
    "title": "event title (for create)",
    "start_time": "ISO 8601 datetime with timezone {timezone} (for create/list)",
    "end_time": "ISO 8601 datetime with timezone {timezone} (for create/list)",
    "description": "event description (for create)",
    "query_date": "ISO 8601 date for filtering (for list queries like 'Friday afternoon', 'tomorrow')"
  }},
  "response": "friendly response to user"
}}

For LIST queries (checking availability or showing events):
- "Am I free Friday afternoon?" → intent: list_calendar, query_date: next Friday's date, start_time: 14:00, end_time: 17:00
- "What's on my calendar tomorrow?" → intent: list_calendar, query_date: tomorrow's date
- "Show events this week" → intent: list_calendar, query_date: {current_date}
- When asking about specific day/time, include query_date AND time range in parameters

Natural time parsing rules (ALWAYS use {current_date} as TODAY in timezone {timezone}):
- "tomorrow at 3pm" → {current_date} + 1 day at 15:00
- "tomorrow afternoon" → {current_date} + 1 day at 14:00, duration 3 hours (2-5pm)
- "tomorrow morning" → {current_date} + 1 day at 09:00, duration 2 hours (9-11am)
- "next Tuesday" → calculate next Tuesday from {current_date} at 10:00, duration 1 hour
- "Friday afternoon" → calculate next Friday from {current_date} at 14:00, duration 3 hours
- "this week" → within 7 days from {current_date}
- "next week" → 7-14 days from {current_date}
- "today at 2pm" → {current_date} at 14:00
- If NO time specified, default to 10:00 AM
- If NO duration specified, default to 1 hour
- For "morning" use 9:00-11:00, "afternoon" use 14:00-17:00, "evening" use 18:00-20:00
- ALWAYS include timezone offset in ISO format (e.g., 2025-10-27T15:00:00+09:00 for Tokyo)

Only use intents: list_calendar, create_event, or general.""",
                            },
                            {"role": "user", "content": message},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.7,
                    },
                    timeout=30.0,
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
                    return await self._handle_calendar_list(user_id, user_claims, params)
                elif intent == "create_event":
                    return await self._handle_calendar_creation_with_params(
                        params, user_id, user_claims, ai_message, timezone
                    )
                else:
                    return {
                        "response": ai_message,
                        "action_taken": "general_response",
                        "success": True,
                    }

        except Exception as e:
            logger.error(f"OpenAI processing error: {e}")
            # Fallback to keyword detection
            if any(keyword in message.lower() for keyword in ["calendar", "show", "list", "view"]):
                return await self._handle_calendar_list(user_id, user_claims)
            return {
                "response": "I had trouble understanding that. Could you try rephrasing?",
                "action_taken": "error",
                "success": False,
            }

    async def _handle_calendar_creation_with_params(
        self,
        params: Dict[str, Any],
        user_id: str,
        user_claims: Optional[Dict[str, Any]],
        ai_message: str,
        timezone: str = "UTC",
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
                    "success": False,
                }

            # Get Google access token
            google_token = (
                await get_google_access_token_from_auth0(user_claims) if user_claims else None
            )

            if not google_token:
                # Log without creating
                audit_log.log_action(
                    user_id=user_id,
                    action="calendar_create_attempt",
                    details={
                        "title": title,
                        "note": "No Google token - would create in real calendar",
                    },
                    success=True,
                )
                return {
                    "response": f"📅 Preview: This event would be created in your Google Calendar. (Authenticate with Google Calendar to create real events)",
                    "action_taken": "calendar_create",
                    "success": True,
                }

            # Check for conflicts
            calendar_client = GoogleCalendarClient(google_token)
            conflicts = await calendar_client.check_conflicts(start_time, end_time)

            conflict_warning = ""
            if conflicts:
                conflict_names = [c.get("summary", "Untitled") for c in conflicts[:3]]
                if len(conflicts) == 1:
                    conflict_warning = f"\n\n⚠️ **Conflict detected:** You already have '{conflict_names[0]}' scheduled at this time."
                elif len(conflicts) <= 3:
                    conflict_warning = f"\n\n⚠️ **Conflicts detected:** You have {len(conflicts)} events at this time: {', '.join(conflict_names)}"
                else:
                    conflict_warning = f"\n\n⚠️ **Conflicts detected:** You have {len(conflicts)} events scheduled during this time."

            # Create real event
            event = await calendar_client.create_event(
                title=title, start_time=start_time, end_time=end_time, description=description
            )

            audit_log.log_action(
                user_id=user_id,
                action="calendar_create",
                details={
                    "title": title,
                    "start": start_time,
                    "event_id": event.get("id"),
                    "had_conflicts": len(conflicts) > 0,
                },
                success=True,
            )

            return {
                "response": f"✅ Successfully created event in your Google Calendar.{conflict_warning}",
                "action_taken": "calendar_create",
                "success": True,
                "event": event,
                "conflicts": conflicts if conflicts else None,
            }

        except Exception as e:
            logger.error(f"Calendar creation error: {e}")
            return {
                "response": "I had trouble creating that event. Please try again.",
                "action_taken": "calendar_create",
                "success": False,
            }

    async def _handle_calendar_creation(
        self,
        message: str,
        user_id: str,
        user_claims: Optional[Dict[str, Any]] = None,
        timezone: str = "UTC",
    ) -> Dict[str, Any]:
        """Handle calendar event creation (keyword-based fallback)"""
        try:
            # Simple extraction from message
            event_title = message[:100] if len(message) <= 100 else f"{message[:97]}..."

            # Log the action attempt
            audit_log.log_action(
                user_id=user_id,
                action="calendar_create_attempt",
                details={"message": message, "event_title": event_title},
                success=True,
            )

            return {
                "response": f"📅 To create this event, please provide more details like date and time (e.g., 'tomorrow at 2pm').",
                "action_taken": "calendar_create",
                "success": True,
            }

        except Exception as e:
            audit_log.log_action(
                user_id=user_id,
                action="calendar_create_attempt",
                details={"message": message, "error": str(e)},
                success=False,
            )
            return {
                "response": "I encountered an error while trying to create the calendar event.",
                "action_taken": "calendar_create",
                "success": False,
            }

    async def _handle_calendar_list(
        self,
        user_id: str,
        user_claims: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle calendar listing - actually fetch calendar events with optional filtering"""
        try:
            if not user_claims:
                return {
                    "response": "I need authentication info to access your calendar.",
                    "action_taken": "calendar_list",
                    "success": False,
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
                    {"title": "Demo Event 1", "start": "2025-10-21T09:00:00Z"},
                    {"title": "Demo Event 3", "start": "2025-10-21T14:00:00Z"},
                ]
                response_text = "📅 Retrieved your upcoming events from Google Calendar (showing mock data - add Calendar scopes to see real events)."
            else:
                # Use real Google Calendar API
                calendar_client = GoogleCalendarClient(google_token)
                events = await calendar_client.list_events(max_results=10)

                # Filter events if date range specified
                if params:
                    start_time = params.get("start_time")
                    end_time = params.get("end_time")

                    if start_time and end_time:
                        # Filter events within the specified time range
                        from datetime import datetime as dt

                        try:
                            query_start = dt.fromisoformat(start_time.replace("Z", "+00:00"))
                            query_end = dt.fromisoformat(end_time.replace("Z", "+00:00"))

                            filtered_events = []
                            for event in events:
                                event_start = dt.fromisoformat(
                                    event["start"].replace("Z", "+00:00")
                                )
                                # Check if event starts within the query range
                                if query_start <= event_start <= query_end:
                                    filtered_events.append(event)

                            events = filtered_events
                            logger.info(f"Filtered to {len(events)} events in specified time range")
                        except Exception as e:
                            logger.warning(f"Date filtering failed: {e}, showing all events")

                if not events:
                    response_text = "📅 You have no upcoming calendar events."
                else:
                    response_text = (
                        f"📅 Retrieved {len(events)} upcoming events from your Google Calendar."
                    )

            # Log the action
            audit_log.log_action(
                user_id=user_id,
                action="calendar_list_attempt",
                details={"events_count": len(events), "real_data": bool(google_token)},
                success=True,
            )

            return {
                "response": response_text,
                "action_taken": "calendar_list",
                "success": True,
                "events": events,  # Include actual event data
            }

        except Exception as e:
            logger.error(f"Calendar list error in AI agent: {e}")
            audit_log.log_action(
                user_id=user_id,
                action="calendar_list_attempt",
                details={"error": str(e)},
                success=False,
            )
            return {
                "response": "I encountered an error while retrieving your calendar events.",
                "action_taken": "calendar_list",
                "success": False,
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
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://vaultmind-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.0.0"}


@app.post("/agent/chat", response_model=ChatResponse)
@limiter.limit("10/minute")
async def chat_with_agent(request: Request, chat_request: ChatRequest, user_claims: Dict[str, Any] = Depends(verify_jwt)):
    """
    Chat with AI agent endpoint
    Security: Requires valid Auth0 JWT, validates input, logs all actions
    Rate limit: 10 requests per minute to control OpenAI API costs
    """
    user_id = user_claims.get("sub", "unknown")

    try:
        # Process message with AI agent
        result = await ai_agent.process_message(
            chat_request.message, user_id, user_claims, timezone=chat_request.timezone
        )

        # Log the chat interaction
        audit_log.log_action(
            user_id=user_id,
            action="chat_interaction",
            details={
                "message": chat_request.message,
                "response": result["response"],
                "action_taken": result.get("action_taken"),
            },
            success=result["success"],
        )

        return ChatResponse(
            response=result["response"],
            action_taken=result.get("action_taken"),
            success=result["success"],
            timestamp=datetime.utcnow(),
            event_details=result.get("event"),  # Single event from creation
            events=result.get("events"),  # Multiple events from listing
            conflicts=result.get("conflicts"),  # Conflicting events (if any)
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        audit_log.log_action(
            user_id=user_id,
            action="chat_interaction",
            details={"message": chat_request.message, "error": str(e)},
            success=False,
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/agent/calendar")
async def list_calendar_events(user_claims: Dict[str, Any] = Depends(verify_jwt)):
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
                    "end": "2025-10-20T10:00:00Z",
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
            success=True,
        )

        return {"events": events, "success": True, "real_data": bool(google_token)}

    except Exception as e:
        logger.error(f"Calendar list error: {e}")
        audit_log.log_action(
            user_id=user_id, action="calendar_list", details={"error": str(e)}, success=False
        )
        raise HTTPException(status_code=500, detail=f"Unable to retrieve calendar events: {str(e)}")


@app.post("/agent/calendar")
@limiter.limit("20/minute")
async def create_calendar_event(
    request: Request, event: CalendarEvent, user_claims: Dict[str, Any] = Depends(verify_jwt)
):
    """
    Create calendar event endpoint
    Security: Requires valid JWT, validates event data, uses Google Calendar API
    Rate limit: 20 requests per minute
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
                "description": event.description
                or "Mock event - Re-authenticate to create real events",
                "start": event.start_time,
                "end": event.end_time,
                "created": datetime.utcnow().isoformat(),
                "is_mock": True,
            }
        else:
            # Use real Google Calendar API
            calendar_client = GoogleCalendarClient(google_token)
            created_event = await calendar_client.create_event(
                title=event.title,
                start_time=event.start_time,
                end_time=event.end_time,
                description=event.description,
            )
            created_event["is_mock"] = False

        audit_log.log_action(
            user_id=user_id,
            action="calendar_create",
            details={
                "event_title": event.title,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "real_data": bool(google_token),
            },
            success=True,
        )

        return {"event": created_event, "success": True, "real_data": bool(google_token)}

    except Exception as e:
        logger.error(f"Calendar create error: {e}")
        audit_log.log_action(
            user_id=user_id,
            action="calendar_create",
            details={"error": str(e), "event_title": event.title},
            success=False,
        )
        raise HTTPException(status_code=500, detail=f"Unable to create calendar event: {str(e)}")


@app.get("/audit/logs")
@limiter.limit("30/minute")
async def get_audit_logs(request: Request, user_claims: Dict[str, Any] = Depends(verify_jwt)):
    """
    Get audit logs for the authenticated user
    Security: Users can only see their own audit logs
    Rate limit: 30 requests per minute
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
