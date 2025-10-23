#!/bin/bash

# Quick Start Script for Google Calendar Integration
# Run this after setting up Google OAuth2 credentials

set -e

echo "🚀 VaultMind - Google Calendar Setup"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the backend/ directory"
    exit 1
fi

# Install Google Calendar dependencies
echo "📦 Installing Google Calendar API dependencies..."
pip install google-auth==2.25.2 google-auth-oauthlib==1.2.0 google-api-python-client==2.111.0

echo "✅ Dependencies installed!"
echo ""

# Check environment variables
echo "🔍 Checking configuration..."
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env file with your Auth0 configuration"
    exit 1
fi

source .env

if [ -z "$AUTH0_DOMAIN" ]; then
    echo "❌ Error: AUTH0_DOMAIN not set in .env"
    exit 1
fi

if [ -z "$AUTH0_AUDIENCE" ]; then
    echo "❌ Error: AUTH0_AUDIENCE not set in .env"
    exit 1
fi

echo "✅ Auth0 configuration found"
echo "   Domain: $AUTH0_DOMAIN"
echo "   Audience: $AUTH0_AUDIENCE"
echo ""

# Prompt for Google credentials (optional)
echo "📋 Google OAuth2 Configuration (Optional)"
echo "=========================================="
echo ""
echo "To use real Google Calendar, you need:"
echo "1. Google Cloud Project with Calendar API enabled"
echo "2. OAuth2 credentials configured in Auth0"
echo ""
echo "See GOOGLE_OAUTH_SETUP.md for detailed instructions"
echo ""

read -p "Have you completed Google OAuth2 setup? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "✅ Great! Make sure you've:"
    echo "   1. ✅ Created Google Cloud project"
    echo "   2. ✅ Enabled Calendar API"
    echo "   3. ✅ Created OAuth2 credentials"
    echo "   4. ✅ Updated Auth0 Google connection with Calendar scopes:"
    echo "      • https://www.googleapis.com/auth/calendar.events"
    echo "      • https://www.googleapis.com/auth/calendar.readonly"
    echo "   5. ✅ Added Auth0 callback URL to Google Console"
    echo ""
    echo "⚠️  IMPORTANT: Users must LOG OUT and LOG BACK IN to get new scopes!"
    echo ""
else
    echo ""
    echo "📝 No problem! The app will use mock calendar data until you complete setup."
    echo "   Follow GOOGLE_OAUTH_SETUP.md when you're ready."
    echo ""
fi

# Start server
echo "🚀 Starting FastAPI backend server..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
