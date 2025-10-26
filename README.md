# 🔐 VaultMind: Secure AI Calendar Assistant

> **Live Demo**: [https://vaultmind-app.vercel.app](https://vaultmind-app.vercel.app)  
> **Video Demo**: [Watch on YouTube](https://youtu.be/Pv8nke_2LM4)

An enterprise-grade AI calendar assistant demonstrating secure AI agent development using **Auth0 for AI**. Features natural language calendar management with real Google Calendar integration, JWT validation, rate limiting, content moderation, and comprehensive audit logging.

**Built for the Auth0 AI Agents Challenge** 🏆

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Auth0 account
- OpenAI API key

### Backend Setup (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your Auth0 and OpenAI credentials

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup (Next.js)

```bash
cd frontend
npm install

# Copy and configure environment
cp .env.example .env.local
# Edit .env.local with your Auth0 configuration

# Run the development server
npm run dev
```

Visit `http://localhost:3000` to see the application!

## 🔒 Security Architecture

### 1. **Auth0 JWT Validation**
- **JWKS Caching**: Backend fetches and caches Auth0's public keys for JWT signature verification
- **Token Validation**: Every API request validates JWT signature, issuer, audience, and expiration
- **User Claims**: Extracts user identity securely from verified JWT tokens

```python
# Secure JWT validation with caching
async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    # Validates against Auth0 JWKS, checks signature, issuer, audience
    payload = jwt.decode(token, public_key, algorithms=["RS256"])
    return payload
```

### 2. **Comprehensive Audit Logging**
- **Action Tracking**: Every agent action is logged with user context
- **Security Context**: Logs include user ID, timestamp, action details, and success status
- **Privacy Compliant**: Logs user actions without storing sensitive content

```python
class AuditLog:
    def log_action(self, user_id: str, action: str, details: Dict, success: bool):
        # Comprehensive logging for security and compliance
```

### 4. **Input Validation & Sanitization**
- **Pydantic Models**: All API inputs validated using Pydantic schemas
- **Length Limits**: Chat messages limited to prevent abuse
- **Action Whitelisting**: AI agent only performs approved actions

## 🏗️ Project Structure

```
vaultmind/
├── backend/                      # FastAPI backend
│   ├── main.py                  # Main app with AI agent, security, rate limiting
│   ├── app/
│   │   ├── auth0_management.py  # Auth0 JWT validation & user management
│   │   └── google_calendar.py   # Google Calendar API integration
│   ├── requirements.txt         # Python dependencies
│   ├── test_*.py               # Comprehensive test suite
│   ├── RATE_LIMITING.md        # Rate limiting documentation
│   ├── CONTENT_MODERATION.md   # Moderation documentation
│   └── .env.example            # Environment template
├── frontend/                     # Next.js 15 frontend
│   ├── app/
│   │   ├── page.tsx            # Landing page with demo video
│   │   ├── chat/               # AI chat interface
│   │   ├── validation/         # Security dashboard
│   │   ├── layout.tsx          # Auth0 UserProvider
│   │   └── api/
│   │       ├── auth/           # Auth0 routes
│   │       ├── chat/           # Chat API proxy
│   │       └── waitlist/       # Waitlist API
│   ├── components/             # React components
│   └── .env.example           # Environment template
├── GOOGLE_OAUTH_SETUP.md        # Google Calendar setup guide
├── AUTH0_SETUP.md              # Auth0 configuration guide
└── README.md                   # This file
```

## 🔧 Configuration

### Quick Start: Automated Auth0 Setup

1. **Create Auth0 Application** (Single Page Application)
2. **Create Auth0 API** with identifier `https://vaultmind-api`
3. **Enable Google Social Connection**
4. **Configure Callback URLs**: `http://localhost:3000/api/auth/callback`
5. **Set Environment Variables** (see below)

### Understanding the Auth0 Flow

- Complete authentication flow diagrams
- JWT token structure and validation
- Security features explanation
- Troubleshooting common issues

### Environment Variables

```bash
# Backend (.env)
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=https://vaultmind-api

# Frontend (.env.local)
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_SECRET=$(openssl rand -hex 32)
```

### OpenAI Setup (Optional)
- Get API key from OpenAI Dashboard: https://platform.openai.com/api-keys
- Add to backend `.env`: `OPENAI_API_KEY=sk-...`
- **Not required**: App uses mock AI responses if not configured

### Google Calendar Setup (Optional but Recommended)
To access **real** Google Calendar data instead of mock events:
   - Create Google Cloud project and enable Calendar API
   - Create OAuth2 credentials
   - Update Auth0 Google connection with Calendar scopes
   - Users must re-authenticate to get new permissions

**Note**: Without Google setup, the app works perfectly with mock calendar data!

## 🚀 Deployment

### Backend (Render.com - Free Tier)

1. Connect GitHub repository to Render
2. Choose "Web Service" and select backend folder
3. Configure environment variables in Render dashboard
4. Deploy automatically on git push

### Frontend (Vercel - Free Tier)

1. Connect GitHub repository to Vercel
2. Choose "Next.js" preset and select frontend folder
3. Configure environment variables in Vercel dashboard
4. Deploy automatically on git push

## 🔍 API Endpoints

### Health Check
```bash
GET /health
# Returns: {"status": "healthy", "timestamp": "...", "version": "1.0.0"}
```

### Chat with AI Agent
```bash
POST /agent/chat
Authorization: Bearer <auth0-jwt>
Content-Type: application/json

{
  "message": "Create a meeting for tomorrow at 2pm"
}
```

### Calendar Operations
```bash
# List events
GET /agent/calendar
Authorization: Bearer <auth0-jwt>

# Create event  
POST /agent/calendar
Authorization: Bearer <auth0-jwt>
{
  "title": "Team Meeting",
  "start_time": "2025-10-20T14:00:00Z",
  "end_time": "2025-10-20T15:00:00Z"
}
```

### Audit Logs
```bash
GET /audit/logs
Authorization: Bearer <auth0-jwt>
# Returns user's own audit trail
```

## 🛡️ Security Features

### ✅ **Authentication & Authorization**
- OAuth2 with Google via Auth0
- JWT signature verification using JWKS
- User-scoped API access

### ✅ **Token Security**
- Short-lived access tokens from Auth0
- No stored refresh tokens
- Secure token management via Auth0 Management API

### ✅ **Input Validation**
- Pydantic schema validation
- SQL injection prevention
- XSS protection via React

### ✅ **Audit & Compliance**
- Complete action logging
- User activity tracking
- Privacy-compliant data handling

### ✅ **Network Security**
- CORS properly configured
- HTTPS in production (via hosting)
- Rate limiting ready (add middleware)
- Validation of OpenAI responses to prevent prompt injection

## 🎯 Auth0 Challenge Features

### **MVP Ready**
- ✅ Working Auth0 login flow
- ✅ Secure chat interface
- ✅ AI agent with calendar integration
- ✅ Complete audit logging
- ✅ Deploy-ready configuration

### **Demo Script**
1. **Show Authentication**: Login with Google OAuth2
2. **Demonstrate Security**: Show JWT validation in browser dev tools
3. **AI Interaction**: Chat with agent to create calendar events
4. **Audit Trail**: Display security logs for all actions

### **Scaling Ready**
- Database integration (SQLite → PostgreSQL)
- Redis for caching and rate limiting
- Container deployment (Docker)
- Monitoring and alerting

## 🧪 Testing

### Backend Tests
```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```


## �🐛 Troubleshooting

### Common Issues

1. **JWT Validation Fails**:
   - Check AUTH0_DOMAIN and AUTH0_AUDIENCE match
   - Verify JWKS endpoint is accessible
   - Ensure clock synchronization

2. **CORS Errors**:
   - Update CORS origins in FastAPI main.py
   - Check frontend URL matches allowed origins

3. **Auth0 Login Issues**:
   - Verify callback URLs in Auth0 dashboard
   - Check environment variables match

### Development Tips

- Use browser dev tools to inspect JWT tokens
- Check backend logs for detailed error messages
- Monitor Auth0 logs for authentication issues

## 📚 Further Reading

- [Auth0 for AI Agents Documentation](https://auth0.com/docs)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Auth0 SDK](https://github.com/auth0/nextjs-auth0)
- [Token Vault Best Practices](https://oauth.net/2/token-exchange/)