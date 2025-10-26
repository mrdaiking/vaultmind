#!/bin/bash
# Add structured logging tags to backend files

echo "Adding [CALENDAR] and [AUTH] tags to google_calendar.py..."

# Backup
cp google_calendar.py google_calendar.py.bak

# CALENDAR tags
sed -i '' 's/logger\.info("Google Calendar service initialized/logger.info("[CALENDAR] Google Calendar service initialized/g' google_calendar.py
sed -i '' 's/logger\.error(f"Failed to initialize Calendar service/logger.error(f"[CALENDAR][ERROR] Failed to initialize Calendar service/g' google_calendar.py
sed -i '' 's/logger\.info(f"Retrieved {len(formatted_events)} calendar events/logger.info(f"[CALENDAR] Retrieved {len(formatted_events)} calendar events/g' google_calendar.py
sed -i '' 's/logger\.error(f"Google Calendar API error:/logger.error(f"[CALENDAR][ERROR] Google Calendar API error:/g' google_calendar.py
sed -i '' 's/logger\.error(f"Unexpected error listing events:/logger.error(f"[CALENDAR][ERROR] Unexpected error listing events:/g' google_calendar.py
sed -i '' 's/logger\.info(f"Created calendar event:/logger.info(f"[CALENDAR] ✅ Created calendar event:/g' google_calendar.py
sed -i '' 's/logger\.error(f"Unexpected error creating event:/logger.error(f"[CALENDAR][ERROR] Unexpected error creating event:/g' google_calendar.py
sed -i '' 's/logger\.info(f"Deleted calendar event:/logger.info(f"[CALENDAR] ✅ Deleted calendar event:/g' google_calendar.py
sed -i '' 's/logger\.error(f"Unexpected error deleting event:/logger.error(f"[CALENDAR][ERROR] Unexpected error deleting event:/g' google_calendar.py
sed -i '' 's/logger\.info(f"Updated calendar event:/logger.info(f"[CALENDAR] ✅ Updated calendar event:/g' google_calendar.py
sed -i '' 's/logger\.error(f"Unexpected error updating event:/logger.error(f"[CALENDAR][ERROR] Unexpected error updating event:/g' google_calendar.py
sed -i '' 's/logger\.info(f"Found {len(conflicts)} potential conflicts/logger.info(f"[CALENDAR] Found {len(conflicts)} potential conflicts/g' google_calendar.py
sed -i '' 's/logger\.error(f"Error checking conflicts:/logger.error(f"[CALENDAR][ERROR] Error checking conflicts:/g' google_calendar.py

# AUTH tags
sed -i '' 's/logger\.info("✅ Found Google access token in JWT custom claim (namespaced)")/logger.info("[AUTH] ✅ Found Google access token in JWT custom claim (namespaced)")/g' google_calendar.py
sed -i '' 's/logger\.info("✅ Found Google access token in JWT custom claim (non-namespaced)")/logger.info("[AUTH] ✅ Found Google access token in JWT custom claim (non-namespaced)")/g' google_calendar.py
sed -i '' 's/logger\.info("💡 No token in JWT, trying Auth0 Management API\.\.\.")/logger.info("[AUTH] 💡 No token in JWT, trying Auth0 Management API\.\.\.")/g' google_calendar.py
sed -i '' 's/logger\.info("✅ Found Google access token in identities array")/logger.info("[AUTH] ✅ Found Google access token in identities array")/g' google_calendar.py
sed -i '' 's/logger\.warning("❌ No Google access token found via any method")/logger.warning("[AUTH] ❌ No Google access token found via any method")/g' google_calendar.py
sed -i '' 's/logger\.debug(f"Available claims:/logger.debug(f"[AUTH] Available claims:/g' google_calendar.py

echo "✅ Added tags to google_calendar.py"
echo ""
echo "Tagged logging patterns:"
echo "  [MGMT] - Auth0 Management API operations (auth0_management.py)"
echo "  [CALENDAR] - Google Calendar API operations (google_calendar.py)"  
echo "  [AUTH] - Authentication/token retrieval (google_calendar.py)"
echo ""
echo "Still need to add to main.py:"
echo "  [AI] - OpenAI/AI agent operations"
echo "  [API] - FastAPI endpoints"
echo "  [AUTH] - JWT validation"
