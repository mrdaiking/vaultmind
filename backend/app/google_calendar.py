"""
Created by Felix
Date: 2025-10-26
Description:
Google Calendar API integration using OAuth2 access tokens from Auth0
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import Management API helper
from app.auth0_management import get_google_access_token_from_management_api
from app.auth0_ai_adapter import get_google_token_via_langchain

logger = logging.getLogger(__name__)


class GoogleCalendarClient:
    """
    Google Calendar API client with OAuth2 token handling
    Security: Uses short-lived access tokens from Auth0
    """
    
    def __init__(self, user_id: str, auth0_management, use_langchain: bool = False):
        """
        Initialize Google Calendar client with Auth0 management
        
        Args:
            user_id: Auth0 user ID (sub)
            auth0_management: Auth0 management client instance
            use_langchain: Whether to use auth0_ai_langchain for token exchange
        """
        self.user_id = user_id
        self.auth0_management = auth0_management
        self.use_langchain = use_langchain  # Feature flag
        self.logger = logging.getLogger(__name__)
        self.service = None  # Lazy-initialized
        self.access_token = None  # Will be fetched when needed
        
    async def _get_refresh_token(self) -> Optional[str]:
        """
        Get refresh token for the user from Auth0 Management API.
        Note: This requires the user to have authenticated with offline_access scope.
        """
        try:
            # Get user's identities from Auth0 Management API
            user_data = await self.auth0_management.get_user_profile(self.user_id)
            
            # Look for google-oauth2 identity with refresh token
            identities = user_data.get("identities", [])
            for identity in identities:
                if identity.get("provider") == "google-oauth2":
                    refresh_token = identity.get("refresh_token")
                    if refresh_token:
                        self.logger.info(f"[CALENDAR] Found refresh token for user {self.user_id}")
                        return refresh_token
            
            self.logger.warning(f"[CALENDAR] No refresh token found for user {self.user_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"[CALENDAR][ERROR] Failed to get refresh token: {e}")
            return None
    
    async def _get_credentials(self) -> Optional[Credentials]:
        """Get Google Calendar credentials with optional langchain path."""
        try:
            if self.use_langchain:
                # Use auth0_ai_langchain
                self.logger.info(f"[CALENDAR] Using auth0_ai_langchain for token exchange")
                refresh_token = await self._get_refresh_token()
                if not refresh_token:
                    self.logger.warning("[CALENDAR] No refresh token, falling back to direct API")
                    access_token = await self.auth0_management.get_google_access_token_from_auth0(
                        self.user_id
                    )
                else:
                    access_token = await get_google_token_via_langchain(
                        self.user_id, 
                        refresh_token
                    )
            else:
                # Use existing direct API calls
                self.logger.info(f"[CALENDAR] Using direct Auth0 API for token exchange")
                access_token = await self.auth0_management.get_google_access_token_from_auth0(
                    self.user_id
                )
            
            if not access_token:
                self.logger.error("[CALENDAR] Failed to get access token")
                return None
            
            # Store for later use
            self.access_token = access_token
                
            # Create credentials object
            credentials = Credentials(
                token=access_token,
                refresh_token=None,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=None,
                client_secret=None
            )
            
            return credentials
            
        except Exception as e:
            self.logger.error(f"[CALENDAR][ERROR] Credential fetch failed: {e}")
            return None
    
    async def _get_service(self):
        """Get or create Google Calendar API service with fresh credentials"""
        if not self.service or not self.access_token:
            try:
                # Get credentials (handles both langchain and direct API paths)
                credentials = await self._get_credentials()
                
                if not credentials:
                    raise Exception("Failed to obtain Google Calendar credentials")
                
                # Build Calendar API service
                self.service = build('calendar', 'v3', credentials=credentials)
                logger.info("[CALENDAR] Google Calendar service initialized")
            except Exception as e:
                logger.error(f"[CALENDAR][ERROR] Failed to initialize Calendar service: {e}")
                raise
        
        return self.service
    
    async def list_events(
        self,
        max_results: int = 10,
        time_min: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        List upcoming calendar events
        
        Args:
            max_results: Maximum number of events to return
            time_min: Minimum event start time (defaults to now)
            
        Returns:
            List of calendar events with id, title, start, end
        """
        try:
            service = await self._get_service()
            
            # Default to events from now onwards
            if not time_min:
                time_min = datetime.utcnow()
            
            # Call Google Calendar API
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Transform to simplified format
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                formatted_events.append({
                    'id': event.get('id'),
                    'title': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'start': start,
                    'end': end,
                    'location': event.get('location', ''),
                    'attendees': [
                        attendee.get('email') 
                        for attendee in event.get('attendees', [])
                    ]
                })
            
            logger.info(f"[CALENDAR] Retrieved {len(formatted_events)} calendar events")
            return formatted_events
            
        except HttpError as e:
            logger.error(f"[CALENDAR][ERROR] Google Calendar API error: {e}")
            raise Exception(f"Failed to list calendar events: {e.reason}")
        except Exception as e:
            logger.error(f"[CALENDAR][ERROR] Unexpected error listing events: {e}")
            raise
    
    async def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new calendar event
        
        Args:
            title: Event title/summary
            start_time: ISO format start time
            end_time: ISO format end time
            description: Optional event description
            location: Optional event location
            attendees: Optional list of attendee email addresses
            
        Returns:
            Created event details
        """
        try:
            service = await self._get_service()
            
            # Build event object
            event_body = {
                'summary': title,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
            }
            
            if description:
                event_body['description'] = description
                
            if location:
                event_body['location'] = location
                
            if attendees:
                event_body['attendees'] = [
                    {'email': email} for email in attendees
                ]
            
            # Create event via API
            created_event = service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            
            logger.info(f"[CALENDAR] ✅ Created calendar event: {created_event.get('id')}")
            
            return {
                'id': created_event.get('id'),
                'title': created_event.get('summary'),
                'description': created_event.get('description', ''),
                'start': created_event['start'].get('dateTime'),
                'end': created_event['end'].get('dateTime'),
                'link': created_event.get('htmlLink'),
                'status': created_event.get('status')
            }
            
        except HttpError as e:
            logger.error(f"[CALENDAR][ERROR] Google Calendar API error: {e}")
            raise Exception(f"Failed to create calendar event: {e.reason}")
        except Exception as e:
            logger.error(f"[CALENDAR][ERROR] Unexpected error creating event: {e}")
            raise
    
    async def delete_event(self, event_id: str) -> bool:
        """
        Delete a calendar event
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if deleted successfully
        """
        try:
            service = await self._get_service()
            
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"[CALENDAR] ✅ Deleted calendar event: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"[CALENDAR][ERROR] Google Calendar API error: {e}")
            raise Exception(f"Failed to delete calendar event: {e.reason}")
        except Exception as e:
            logger.error(f"[CALENDAR][ERROR] Unexpected error deleting event: {e}")
            raise
    
    async def update_event(
        self,
        event_id: str,
        title: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing calendar event
        
        Args:
            event_id: Google Calendar event ID
            title: Optional new title
            start_time: Optional new start time (ISO format)
            end_time: Optional new end time (ISO format)
            description: Optional new description
            
        Returns:
            Updated event details
        """
        try:
            service = await self._get_service()
            
            # Get existing event
            event = service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Update fields
            if title:
                event['summary'] = title
            if description:
                event['description'] = description
            if start_time:
                event['start'] = {
                    'dateTime': start_time,
                    'timeZone': 'UTC'
                }
            if end_time:
                event['end'] = {
                    'dateTime': end_time,
                    'timeZone': 'UTC'
                }
            
            # Update via API
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"[CALENDAR] ✅ Updated calendar event: {event_id}")
            
            return {
                'id': updated_event.get('id'),
                'title': updated_event.get('summary'),
                'description': updated_event.get('description', ''),
                'start': updated_event['start'].get('dateTime'),
                'end': updated_event['end'].get('dateTime'),
                'link': updated_event.get('htmlLink')
            }
            
        except HttpError as e:
            logger.error(f"[CALENDAR][ERROR] Google Calendar API error: {e}")
            raise Exception(f"Failed to update calendar event: {e.reason}")
        except Exception as e:
            logger.error(f"[CALENDAR][ERROR] Unexpected error updating event: {e}")
            raise
    
    async def check_conflicts(
        self,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """
        Check for scheduling conflicts in the given time range
        
        Args:
            start_time: ISO format start time
            end_time: ISO format end time
            
        Returns:
            List of conflicting events
        """
        try:
            service = await self._get_service()
            
            # Query events in the time range
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format conflicts
            conflicts = []
            for event in events:
                conflicts.append({
                    'id': event.get('id'),
                    'title': event.get('summary', 'No Title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date'))
                })
            
            if conflicts:
                logger.info(f"[CALENDAR] Found {len(conflicts)} potential conflicts")
            else:
                logger.info("[CALENDAR] No scheduling conflicts found")
            
            return conflicts
            
        except HttpError as e:
            logger.error(f"[CALENDAR][ERROR] Google Calendar API error: {e}")
            raise Exception(f"Failed to check conflicts: {e.reason}")
        except Exception as e:
            logger.error(f"[CALENDAR][ERROR] Unexpected error checking conflicts: {e}")
            raise


async def get_google_access_token_from_auth0(user_claims: Dict[str, Any]) -> Optional[str]:
    """
    Extract Google OAuth2 access token from Auth0 JWT claims or Management API.
    
    Tries multiple methods in order:
    1. Check JWT custom claims (if Auth0 Action added it)
    2. Fetch from Auth0 Management API (runtime lookup)
    
    Args:
        user_claims: The decoded JWT claims from Auth0
        
    Returns:
        Google access token if found, None otherwise
    """
    # Method 1: Check for namespaced custom claim (if Action worked)
    google_token = user_claims.get("https://vaultmind.app/google_access_token")
    if google_token:
        logger.info("[AUTH] ✅ Found Google access token in JWT custom claim (namespaced)")
        return google_token
    
    # Method 2: Check for non-namespaced custom claim (fallback)
    google_token = user_claims.get("google_access_token")
    if google_token:
        logger.info("[AUTH] ✅ Found Google access token in JWT custom claim (non-namespaced)")
        return google_token
    
    # Method 3: Fetch from Management API (runtime)
    logger.info("[AUTH] 💡 No token in JWT, trying Auth0 Management API...")
    user_sub = user_claims.get("sub")
    if user_sub:
        google_token = await get_google_access_token_from_management_api(user_sub)
        if google_token:
            return google_token
    
    # Method 4: Check identities array in JWT (rarely works)
    identities = user_claims.get("identities", [])
    for identity in identities:
        if identity.get("provider") == "google-oauth2":
            access_token = identity.get("access_token")
            if access_token:
                logger.info("[AUTH] ✅ Found Google access token in identities array")
                return access_token
    
    # Debug: Log available claims
    logger.warning("[AUTH] ❌ No Google access token found via any method")
    logger.debug(f"[AUTH] Available claims: {list(user_claims.keys())}")
    
    return None
